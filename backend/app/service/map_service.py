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
):
    """
    统一入口：优先用高德（AMAP）搜索附近餐厅；
    - 若高德未配置/返回 0/失败，降级到百度；
    - 若两个都配置，则同时调用并合并去重（amap+baidu）。

    返回: (items_list, info_dict)
      items_list: 餐厅列表，每个 item 带 source: "amap" / "baidu" / "amap+baidu"
      info_dict:  {"total_hits": N, "source": "...", "returned": N}

    关键改进：
      - 使用多关键词搜索，避免单搜"美食"遗漏；
      - 利用 API 原生 total/count 字段告知"真实命中总数"；
      - 分页遇到未满页时，再多翻 1 页确认，避免 API 抖动导致数量变化。
    """
    amap_items: List[Dict[str, Any]] = []
    amap_info: Dict[str, Any] = {"total_hits": 0, "source": "amap", "returned": 0}
    amap_err: Optional[str] = None

    baidu_items: List[Dict[str, Any]] = []
    baidu_info: Dict[str, Any] = {"total_hits": 0, "source": "baidu", "returned": 0}
    baidu_err: Optional[str] = None

    # 1) 高德
    if _has_amap_key():
        try:
            items, info = amap_map_service.search_nearby_restaurants(
                query=query,
                region=region,
                location=location,
                radius=radius,
                page_size=page_size,
                page_num=page_num,
            )
            amap_items = items
            amap_info = info
            logger.info(f"[amap] 命中 {info.get('total_hits')}，本次返回 {len(items)} 家餐厅")
        except Exception as e:
            amap_err = f"{type(e).__name__}: {e}"
            logger.warning(f"[amap] 搜索失败: {amap_err}")
    else:
        amap_err = "未配置 AMAP_KEY"
        logger.info("[amap] 未配置 AMAP_KEY，跳过高德")

    # 2) 百度（无论高德是否有结果都尝试，用于交叉补充）
    if _has_baidu_ak():
        try:
            items, info = baidu_map_service.search_nearby_restaurants(
                query=query,
                region=region,
                location=location,
                radius=radius,
                page_size=page_size,
                page_num=page_num,
            )
            baidu_items = items
            baidu_info = info
            logger.info(f"[baidu] 命中 {info.get('total_hits')}，本次返回 {len(items)} 家餐厅")
        except Exception as e:
            baidu_err = f"{type(e).__name__}: {e}"
            logger.warning(f"[baidu] 搜索失败: {baidu_err}")
    else:
        baidu_err = "未配置 BAIDU_MAP_AK"
        logger.info("[baidu] 未配置 BAIDU_MAP_AK，跳过百度")

    # 3) 合并 & 去重（两个数据源都有结果时）
    merged_items: List[Dict[str, Any]] = []
    if amap_items and baidu_items:
        merged_items = _dedupe(amap_items, baidu_items)
        info = {
            "total_hits": max(amap_info.get("total_hits", 0), baidu_info.get("total_hits", 0)),
            "source": "amap+baidu",
            "returned": len(merged_items),
            "amap_total": amap_info.get("total_hits", 0),
            "baidu_total": baidu_info.get("total_hits", 0),
        }
        return merged_items, info

    # 4) 只有高德有结果
    if amap_items:
        return amap_items, amap_info

    # 5) 只有百度有结果
    if baidu_items:
        return baidu_items, baidu_info

    # 6) 两者都失败 / 都没结果
    reasons = []
    if amap_err:
        reasons.append(f"高德: {amap_err}")
    if baidu_err:
        reasons.append(f"百度: {baidu_err}")
    if not reasons:
        reasons.append("附近未搜到餐厅，可尝试放大搜索范围")
    raise RuntimeError("；".join(reasons))
