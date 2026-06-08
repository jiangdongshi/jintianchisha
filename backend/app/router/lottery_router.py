import math
import random
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.service.lottery_service import perform_lottery, get_recent_lotteries
from app.service.map_service import search_nearby_restaurants
from app.repo.restaurant_repo import create_restaurant, get_restaurants, delete_all_restaurants
from app.schemas import RestaurantCreate, LotteryResult


router = APIRouter(prefix="/lottery", tags=["lottery"])


@router.post("/draw", response_model=LotteryResult)
def draw_lottery(winner_user_id: str = None, winner_user_name: str = None, db: Session = Depends(get_db)):
    result = perform_lottery(db, winner_user_id=winner_user_id, winner_user_name=winner_user_name)
    if result is None:
        raise HTTPException(status_code=404, detail="No restaurants available")
    return result


@router.get("/history", response_model=list)
def read_lottery_history(limit: int = 10, db: Session = Depends(get_db)):
    records = get_recent_lotteries(db, limit=limit)
    return records


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@router.post("/draw/nearby")
def draw_nearby(
    latitude: float = Query(..., description="用户纬度，例如 39.915"),
    longitude: float = Query(..., description="用户经度，例如 116.404"),
    radius_meters: int = Query(2000, ge=100, le=20000, description="搜索半径（米），推荐 1000~3000"),
    keyword: str = Query("美食", description="关键词，默认 美食"),
    page_size: int = Query(20, ge=1, le=25, description="地图每页的候选数量，1~25"),
    min_budget: Optional[int] = Query(None, ge=0, description="人均预算下限（元），不填则不限制"),
    max_budget: Optional[int] = Query(None, ge=0, description="人均预算上限（元），不填则不限制"),
    import_mode: str = Query("auto", description="auto=自动导入周边餐厅后抽奖；existing=只从已有餐厅里按距离过滤"),
    db: Session = Depends(get_db),
):
    """
    根据用户位置，调用地图 API（高德优先，失败降级到百度）搜索周边餐厅并存库，
    然后随机抽出一家，同时返回步行/打车的估算时间和直线距离。

    预算规则:
      - 只填 min_budget: 挑人均 >= min_budget 的
      - 只填 max_budget: 挑人均 <= max_budget 的
      - 两者都填: 挑区间内的
      - 都不填: 不做预算过滤
      - 价格为空/未知的餐厅: 只有当预算也没限制时才保留
    """
    location_str = f"{latitude:.6f},{longitude:.6f}"

    if import_mode == "auto":
        try:
            items = search_nearby_restaurants(
                query=keyword,
                location=location_str,
                radius=radius_meters,
                page_size=page_size,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"调用地图 API 失败：{e}")

        if not items:
            raise HTTPException(status_code=404, detail="附近没搜到餐厅，试试加大 radius 或换关键词")

        # 切换搜索条件时：先清空旧的备选，确保候选池只包含本次搜索结果
        delete_all_restaurants(db)

        imported_ids = []
        for item in items:
            if not item.get("name"):
                continue
            lat_val = item.get("latitude")
            lng_val = item.get("longitude")
            price_val = item.get("price")
            try:
                price_int = int(price_val) if price_val is not None and str(price_val).strip() else None
            except (ValueError, TypeError):
                price_int = None

            payload = RestaurantCreate(
                name=item["name"],
                description=item.get("description") or "",
                address=item.get("address") or "",
                phone=item.get("phone") or "",
                rating=item.get("rating"),
                price=price_int,
                tags=item.get("tags") or "",
                image_url="",
                latitude=str(lat_val) if lat_val is not None and lat_val != "" else "",
                longitude=str(lng_val) if lng_val is not None and lng_val != "" else "",
            )
            db_obj = create_restaurant(db, payload)
            imported_ids.append(db_obj.id)

        pool = get_restaurants(db)
    else:
        all_r = get_restaurants(db)
        pool = []
        for r in all_r:
            try:
                lat2 = float(r.latitude)
                lng2 = float(r.longitude)
            except (TypeError, ValueError):
                continue
            if _haversine_m(latitude, longitude, lat2, lng2) <= radius_meters:
                pool.append(r)

    # 预算过滤
    budget_filtered = []
    for r in pool:
        price = getattr(r, "price", None)
        if min_budget is not None or max_budget is not None:
            if price is None or price <= 0:
                # 价格未知的餐厅，在预算过滤模式下跳过（避免误匹配）
                continue
            if min_budget is not None and price < min_budget:
                continue
            if max_budget is not None and price > max_budget:
                continue
        budget_filtered.append(r)
    pool = budget_filtered

    if not pool:
        if min_budget is not None or max_budget is not None:
            raise HTTPException(
                status_code=404,
                detail=f"附近没有人均 {min_budget or 0}-{max_budget or '∞'} 元的餐厅，试试放宽预算或扩大半径",
            )
        raise HTTPException(status_code=404, detail="没有符合条件的餐厅，请先导入或调整参数")

    picked = random.choice(pool)

    try:
        p_lat = float(picked.latitude)
        p_lng = float(picked.longitude)
        distance_m = _haversine_m(latitude, longitude, p_lat, p_lng)
    except (TypeError, ValueError):
        distance_m = 0

    distance_km = round(distance_m / 1000.0, 2)
    walk_min = max(1, int(distance_m / 80.0))  # 步行 ≈ 80米/分钟
    drive_min = max(1, int(distance_m / 450.0))  # 打车 ≈ 450米/分钟

    return {
        "restaurant": {
            "id": picked.id,
            "name": picked.name,
            "address": picked.address,
            "phone": picked.phone,
            "rating": picked.rating,
            "price": getattr(picked, "price", None),
            "tags": picked.tags,
        },
        "distance_km": distance_km,
        "walk_min": walk_min,
        "drive_min": drive_min,
        "pool_size": len(pool),
    }
