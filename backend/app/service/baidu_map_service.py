import math
import ssl
import urllib.request
import urllib.parse
import json
from typing import Optional, List, Dict, Any
from app.config import settings


BAIDU_PLACE_URL = "https://api.map.baidu.com/place/v2/search"

# 搜索策略：
#   用一个关键词（默认"美食"）按顺序翻页，真实范围内有多少家就返回多少家。
#   每页最大 20 条，持续翻页直到 API 返回未满一页或到达 safety_cap（默认 1000）。
#   按 "名称+地址" 去重后返回，按评分降序。
SAFETY_CAP = 1000


def _get_ak() -> str:
    return getattr(settings, "BAIDU_MAP_AK", "") or ""


def _http_get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    query = urllib.parse.urlencode({k: str(v) for k, v in params.items() if v is not None})
    full_url = f"{url}?{query}"

    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": "Mozilla/5.0 jin-tian-chi-sha/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


# =========================================================================
# 坐标转换：WGS-84 (GPS) → BD-09 (百度)
# 浏览器返回的是 WGS-84，百度地图 API 需要 BD-09，偏移约 50~200 米。
# 参考：https://lbsyun.baidu.com/index.php?title=coordinate
# =========================================================================
def _wgs84_to_bd09(lat: float, lng: float) -> (float, float):
    PI = 3.1415926535897932384626
    A = 6378245.0
    EE = 0.00669342162296594323

    def _out_of_china(lat: float, lng: float) -> bool:
        return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)

    def _transform_lat(x: float, y: float) -> float:
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * PI) + 320 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
        return ret

    def _transform_lng(x: float, y: float) -> float:
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
        return ret

    if _out_of_china(lat, lng):
        gcj_lat, gcj_lng = lat, lng
    else:
        dlat = _transform_lat(lng - 105.0, lat - 35.0)
        dlng = _transform_lng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * PI
        magic = math.sin(radlat)
        magic = 1 - EE * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
        dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
        gcj_lat = lat + dlat
        gcj_lng = lng + dlng

    X_PI = PI * 3000.0 / 180.0
    z = math.sqrt(gcj_lng * gcj_lng + gcj_lat * gcj_lat) + 0.00002 * math.sin(gcj_lat * X_PI)
    theta = math.atan2(gcj_lat, gcj_lng) + 0.000003 * math.cos(gcj_lng * X_PI)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return round(bd_lat, 6), round(bd_lng, 6)


# =========================================================================
# 单次搜索
# =========================================================================
def _fetch_one_page(
    ak: str,
    query: str,
    location_str: str,
    radius: int,
    page_size: int,
    page_num: int,
) -> List[Dict[str, Any]]:
    params = {
        "query": query,
        "tag": "美食",
        "output": "json",
        "ak": ak,
        "page_size": page_size,
        "page_num": page_num,
        "scope": 2,
        "location": location_str,
        "radius": radius,
    }
    data = _http_get(BAIDU_PLACE_URL, params)
    status = data.get("status")
    if status != 0:
        raise RuntimeError(
            f"百度地图 API 错误 status={status}, message={data.get('message')}"
        )
    return data.get("results") or []


def _parse_price(val) -> Optional[int]:
    """
    百度 detail_info.price 通常是数字/字符串，但偶尔也是：
      "100" / "100元/人" / "人均 98" / "88-168元"
    统一解析成第一个数字（区间取最小值）。
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    import re
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-–~]+\s*(\d+(?:\.\d+)?)", s)
    if m:
        try:
            return int(float(m.group(1)))
        except (ValueError, TypeError):
            pass
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return int(float(m.group(0)))
    except (ValueError, TypeError):
        return None


def _parse_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for item in results:
        loc = item.get("location") or {}
        detail_info = item.get("detail_info") or {}
        name = (item.get("name") or "").strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "address": item.get("address") or "",
                "phone": item.get("telephone") or "",
                "latitude": loc.get("lat"),
                "longitude": loc.get("lng"),
                "rating": _parse_rating(detail_info.get("overall_rating")),
                "price": _parse_price(detail_info.get("price")),
                "tags": detail_info.get("tag") or "",
                "image_url": "",
                "description": (
                    f"{detail_info.get('tag', '')} "
                    f"{'人均' + str(detail_info.get('price')) + '元' if detail_info.get('price') else ''}"
                ).strip(),
                "source": "baidu_map",
            }
        )
    return out


def search_nearby_restaurants(
    query: str = "美食",
    region: Optional[str] = None,
    location: Optional[str] = None,
    radius: int = 2000,
    page_size: int = 20,
    page_num: int = 0,
) -> List[Dict[str, Any]]:
    """
    按坐标搜索周边餐厅（百度地图）：
      1. 坐标 WGS-84 → BD-09 转换；
      2. 用单一关键词（默认"美食"）按顺序翻页，真实范围内有多少家就返回多少；
      3. 按 "名称+地址" 去重，按评分降序。

    参数:
      - location: "纬度,经度"
      - radius: 搜索半径（米），100~50000
      - page_size: 1~20（单页数量）
      - query: 关键词（默认 美食）
    """
    ak = _get_ak()
    if not ak:
        raise RuntimeError("未配置 BAIDU_MAP_AK，请到 .env 设置百度地图开放平台的 AK")

    # 1) 坐标转换
    location_str = location
    if location and "," in location:
        try:
            lat_s, lng_s = location.split(",")
            lat = float(lat_s.strip())
            lng = float(lng_s.strip())
            bd_lat, bd_lng = _wgs84_to_bd09(lat, lng)
            location_str = f"{bd_lat},{bd_lng}"
        except (ValueError, TypeError):
            location_str = location

    # 2) 单一关键词按页码翻页，直到 API 返回未满一页或达到 safety_cap
    kw = (query or "美食").strip() or "美食"
    seen: Dict[str, Dict[str, Any]] = {}
    ps = max(10, min(20, page_size))  # 百度每页最大 20

    page_idx = 0
    while True:
        try:
            page = _fetch_one_page(
                ak=ak,
                query=kw,
                location_str=location_str,
                radius=min(radius, 50000),
                page_size=ps,
                page_num=page_idx,
            )
        except RuntimeError as e:
            if page_idx == 0:
                raise e
            break
        if not page:
            break
        for item in _parse_results(page):
            key_str = item["name"] + "|" + str(item.get("address") or "")
            if key_str not in seen:
                seen[key_str] = item
        if len(seen) >= SAFETY_CAP:
            break
        if len(page) < ps:
            break
        page_idx += 1

    # 3) 排序：评分降序，有价格信息优先
    all_items = list(seen.values())
    all_items.sort(
        key=lambda x: (
            -(x.get("rating") or 0),
            0 if (x.get("price") is not None and x.get("price") != "") else 1,
        )
    )

    return all_items


def _parse_rating(val) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        rating = float(val)
        return max(1, min(5, int(round(rating))))
    except (ValueError, TypeError):
        return None
