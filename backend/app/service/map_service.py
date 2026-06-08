import logging
from typing import Optional, List, Dict, Any

from app.config import settings
from app.service import amap_map_service
from app.service import baidu_map_service

logger = logging.getLogger(__name__)


def _has_amap_key() -> bool:
    key = getattr(settings, "AMAP_KEY", "") or ""
    return bool(key) and key not in {"", "your_amap_key"}


def _has_baidu_ak() -> bool:
    ak = getattr(settings, "BAIDU_MAP_AK", "") or ""
    return bool(ak) and ak not in {"", "your_baidu_map_ak"}


def _dedupe(items_a: List[Dict[str, Any]], items_b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并两个搜索结果，按 (name, address) 去重。
    同时，若同一家餐厅某字段为空（例如高德没 price，百度有），互相补齐。
    """
    merged: Dict[str, Dict[str, Any]] = {}
    for item in items_a:
        key = (item.get("name") or "") + "|" + (item.get("address") or "")
        if not item.get("name"):
            continue
        merged[key] = dict(item)

    for item in items_b:
        key = (item.get("name") or "") + "|" + (item.get("address") or "")
        if not item.get("name"):
            continue
        if key in merged:
            # 合并：补齐缺失字段
            existing = merged[key]
            for field in ("rating", "price", "tags", "phone", "latitude", "longitude"):
                if existing.get(field) in (None, "", 0) and item.get(field) not in (None, "", 0):
                    existing[field] = item[field]
            # source 标为 hybrid
            if existing.get("source") != (item.get("source") or ""):
                existing["source"] = f"{existing.get('source','')}+{item.get('source','')}".strip("+")
        else:
            merged[key] = dict(item)

    return list(merged.values())


def search_nearby_restaurants(
    query: str = "美食",
    region: Optional[str] = None,
    location: Optional[str] = None,
    radius: int = 2000,
    page_size: int = 20,
    page_num: int = 0,
) -> List[Dict[str, Any]]:
    """
    统一入口：优先用高德（AMAP）搜索附近餐厅；
    - 若高德未配置/返回 0/失败，降级到百度；
    - 两个都不可用 → 返回友好错误。

    结果中会带上 source: "amap" / "baidu" / "amap+baidu"。
    """
    amap_items: List[Dict[str, Any]] = []
    amap_err: Optional[str] = None

    baidu_items: List[Dict[str, Any]] = []
    baidu_err: Optional[str] = None

    # 1) 优先高德
    if _has_amap_key():
        try:
            amap_items = amap_map_service.search_nearby_restaurants(
                query=query,
                region=region,
                location=location,
                radius=radius,
                page_size=page_size,
                page_num=page_num,
            )
            logger.info(f"[amap] 搜索到 {len(amap_items)} 家餐厅")
        except Exception as e:
            amap_err = f"{type(e).__name__}: {e}"
            logger.warning(f"[amap] 搜索失败，将降级到百度: {amap_err}")
    else:
        amap_err = "未配置 AMAP_KEY"
        logger.info("[amap] 未配置 AMAP_KEY，跳过高德")

    # 2) 高德可用且有结果 → 直接返回（数量随 radius 自然变化）
    if amap_items:
        return amap_items

    # 3) 否则尝试百度（补充 / 回退）
    if _has_baidu_ak():
        try:
            baidu_items = baidu_map_service.search_nearby_restaurants(
                query=query,
                region=region,
                location=location,
                radius=radius,
                page_size=page_size,
                page_num=page_num,
            )
            logger.info(f"[baidu] 搜索到 {len(baidu_items)} 家餐厅")
        except Exception as e:
            baidu_err = f"{type(e).__name__}: {e}"
            logger.warning(f"[baidu] 搜索失败: {baidu_err}")
    else:
        baidu_err = "未配置 BAIDU_MAP_AK"
        logger.info("[baidu] 未配置 BAIDU_MAP_AK，跳过百度")

    # 4) 百度有结果就返回
    if baidu_items:
        return baidu_items

    # 5) 两者都失败 / 都没结果
    reasons = []
    if amap_err:
        reasons.append(f"高德: {amap_err}")
    if baidu_err:
        reasons.append(f"百度: {baidu_err}")
    if not reasons:
        reasons.append("附近未搜到餐厅，可尝试放大搜索范围")
    raise RuntimeError("；".join(reasons))
