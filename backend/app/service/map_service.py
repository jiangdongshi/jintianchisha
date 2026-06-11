import logging
from typing import Optional, List, Dict, Any

from app.config import settings
from app.service import amap_map_service

logger = logging.getLogger(__name__)


def _has_amap_key() -> bool:
    key = getattr(settings, "AMAP_KEY", "") or ""
    return bool(key) and key not in {"", "your_amap_key"}


def search_nearby_restaurants(
    query: str = "美食",
    region: Optional[str] = None,
    location: Optional[str] = None,
    radius: int = 2000,
    page_size: int = 20,
    page_num: int = 0,
):
    """
    地图搜索入口：使用高德（AMAP）搜索附近餐厅。

    返回: (items_list, info_dict)
      items_list: 餐厅列表，每个 item 带 source: "amap"
      info_dict:  {"total_hits": N, "source": "...", "returned": N}
    """
    if not _has_amap_key():
        raise RuntimeError("未配置 AMAP_KEY")

    try:
        items, info = amap_map_service.search_nearby_restaurants(
            query=query,
            region=region,
            location=location,
            radius=radius,
            page_size=page_size,
            page_num=page_num,
        )
    except Exception as e:
        logger.warning(f"[amap] 搜索失败: {type(e).__name__}: {e}")
        raise

    if not items:
        raise RuntimeError("附近未搜到餐厅，可尝试放大搜索范围")

    logger.info(f"[amap] 命中 {info.get('total_hits')}，本次返回 {len(items)} 家餐厅")
    return items, info
