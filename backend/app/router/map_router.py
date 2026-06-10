from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.service.map_service import search_nearby_restaurants
from app.repo.restaurant_repo import create_restaurant, delete_all_restaurants
from app.schemas import RestaurantCreate

router = APIRouter(prefix="/map", tags=["map"])


@router.post("/import")
def import_from_map(
    query: str = Query("美食", description="搜索关键词，如 美食/火锅/日料"),
    location: str = Query(..., description="用户位置：\"纬度,经度\"，例如 39.915,116.404"),
    radius: int = Query(1000, ge=100, le=50000, description="搜索半径（米）"),
    page_size: int = Query(20, ge=1, le=25, description="每页条数"),
    page_num: int = Query(0, ge=0, description="页码"),
    save: bool = Query(False, description="是否直接保存到数据库（保存前会先清空已有餐厅，确保候选集是本次搜索结果）"),
    db: Session = Depends(get_db),
):
    """
    统一地图导入接口：优先调用高德（AMAP），不可用时自动降级到百度（Baidu）。
    - 必须传 `location=39.915,116.404` + `radius=1000`
    - `save=true`：先清空已有餐厅 → 保存本次搜索结果
    - `save=false`：只预览，不修改数据库
    """
    if not location or "," not in location:
        raise HTTPException(status_code=400, detail="location 格式必须为 \"纬度,经度\"，例如 39.915,116.404")
    try:
        lat, lng = location.split(",")
        float(lat.strip())
        float(lng.strip())
    except Exception:
        raise HTTPException(status_code=400, detail="location 格式错误，必须是 \"纬度,经度\"")

    try:
        items, info = search_nearby_restaurants(
            query=query,
            region=None,
            location=location,
            radius=radius,
            page_size=page_size,
            page_num=page_num,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用地图 API 失败：{e}")

    saved_ids = []
    deleted = 0
    if save:
        deleted = delete_all_restaurants(db)
        for item in items:
            if not item.get("name"):
                continue
            lat_val = item.get("latitude")
            lng_val = item.get("longitude")
            payload = RestaurantCreate(
                name=item["name"],
                description=item.get("description") or (f"{item.get('tags','')} " + (f"人均{item.get('price')}元" if item.get('price') else "")).strip(),
                address=item.get("address") or "",
                phone=item.get("phone") or "",
                rating=item.get("rating"),
                price=item.get("price"),
                tags=item.get("tags") or "",
                image_url=item.get("image_url") or "",
                latitude=str(lat_val) if lat_val is not None and lat_val != "" else "",
                longitude=str(lng_val) if lng_val is not None and lng_val != "" else "",
            )
            db_obj = create_restaurant(db, payload)
            saved_ids.append(db_obj.id)

    return {
        "count": len(items),
        "total_hits": info.get("total_hits", len(items)),
        "source": info.get("source", "map"),
        "saved": len(saved_ids),
        "deleted": deleted,
        "saved_ids": saved_ids,
        "items": items,
    }
