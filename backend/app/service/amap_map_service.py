import math
import ssl
import urllib.request
import urllib.parse
import json
from typing import Optional, List, Dict, Any
from app.config import settings


AMAP_AROUND_URL = "https://restapi.amap.com/v3/place/around"

# 多关键词池，与百度保持一致，用于扩大候选
DEFAULT_KEYWORDS = [
    "美食", "火锅", "烧烤", "川菜", "日料",
    "快餐", "小吃", "西餐", "面条", "奶茶",
]


def _get_key() -> str:
    return getattr(settings, "AMAP_KEY", "") or ""


def _http_get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    query = urllib.parse.urlencode(
        {k: str(v) for k, v in params.items() if v is not None}
    )
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
# 坐标转换：WGS-84 (GPS) → GCJ-02 (火星坐标，高德/腾讯)
# 浏览器返回的是 WGS-84，高德需要 GCJ-02，偏移约 50~200 米。
# =========================================================================
def _wgs84_to_gcj02(lat: float, lng: float) -> (float, float):
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
        return round(lat, 6), round(lng, 6)

    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    return round(lat + dlat, 6), round(lng + dlng, 6)


def _parse_rating(val) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        rating = float(val)
        return max(1, min(5, int(round(rating))))
    except (ValueError, TypeError):
        return None


def _parse_price(val) -> Optional[int]:
    """
    高德 POI 的 cost 字段可能是：
      None / "" / "100" / "100元/人" / "人均 98" / "人均¥58" /
      "88-168元" / "￥68起" 等
    统一解析成第一个数字（区间的话取最小值），取不到返回 None。
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    import re
    # 1) 优先匹配 "数字 - 数字" 区间，取最小值
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-–~]+\s*(\d+(?:\.\d+)?)", s)
    if m:
        try:
            return int(float(m.group(1)))
        except (ValueError, TypeError):
            pass
    # 2) 匹配任意整数/小数
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return int(float(m.group(0)))
    except (ValueError, TypeError):
        return None


# =========================================================================
# 单次搜索
# 搜索策略：
#   用一个关键词（默认"美食"）按顺序翻页，真实范围内有多少家就返回多少家。
#   每页最大 25 条，持续翻页直到 API 未满一页或到达 safety_cap（默认 1000）。
#   按 "名称+地址" 去重后返回，按评分降序。
SAFETY_CAP = 1000


def _fetch_one_page(
    key: str,
    keywords: str,
    location_str: str,            # 格式："lng,lat"
    radius: int,
    page_size: int,
    page_num: int,                # 从 1 开始
) -> List[Dict[str, Any]]:
    params = {
        "key": key,
        "keywords": keywords,
        "location": location_str,
        "radius": min(radius, 50000),
        "offset": page_size,
        "page": page_num,
        "extensions": "all",         # all 会返回 rating / cost 等
        "output": "json",
    }
    data = _http_get(AMAP_AROUND_URL, params)
    status = data.get("status")
    if status != "1" and status != 1:
        raise RuntimeError(
            f"高德地图 API 错误 status={status}, info={data.get('info')}, infocode={data.get('infocode')}"
        )
    return data.get("pois") or []


def _parse_pois(pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    把高德 POI 格式统一成和百度解析后一致的 dict 结构：
      name / address / phone / latitude / longitude / rating / price / tags / source
    """
    out = []
    for poi in pois:
        name = (poi.get("name") or "").strip()
        if not name:
            continue

        # location: "116.32,39.98"  (lng,lat) — 注意与百度相反
        loc_str = poi.get("location") or ""
        lat_val: Optional[float] = None
        lng_val: Optional[float] = None
        if loc_str and "," in loc_str:
            try:
                lng_s, lat_s = loc_str.split(",")
                lng_val = float(lng_s.strip())
                lat_val = float(lat_s.strip())
            except (ValueError, TypeError):
                lat_val = None
                lng_val = None

        # tags: 从 type / typecode 中提取"最后一级分类"
        type_raw = poi.get("type") or ""
        tags = ""
        if type_raw:
            parts = [p for p in type_raw.split(";") if p.strip()]
            if parts:
                # 取最后一段，通常就是具体品类（"餐饮服务;快餐厅;肯德基" → "肯德基" or 更好的：取中间段）
                tags = parts[-1]
                # 但 parts[-1] 可能太具体（品牌名），所以取 parts 的后半段通用分类
                if len(parts) >= 2:
                    tags = parts[-2] if len(parts[-2]) <= 8 else parts[-1]

        # 高德把 cost / rating 放在 biz_ext 子字典里：
        #   biz_ext: {"cost": "170.00", "rating": "4.7", "opentime2": "...", ...}
        biz_ext = poi.get("biz_ext") or {}
        if not isinstance(biz_ext, dict):
            biz_ext = {}

        # price: "170.00" / "100-200" 等
        price = _parse_price(biz_ext.get("cost"))

        out.append(
            {
                "name": name,
                "address": poi.get("address") or "",
                "phone": poi.get("tel") or "",
                "latitude": lat_val,
                "longitude": lng_val,
                "rating": _parse_rating(biz_ext.get("rating")),
                "price": price,
                "tags": tags,
                "image_url": "",
                "description": (
                    f"{tags} "
                    f"{'人均' + str(price) + '元' if price else ''}"
                ).strip(),
                "source": "amap",
            }
        )
    return out


def search_nearby_restaurants(
    query: str = "美食",
    region: Optional[str] = None,
    location: Optional[str] = None,
    radius: int = 2000,
    page_size: int = 25,
    page_num: int = 0,
) -> List[Dict[str, Any]]:
    """
    按坐标搜索周边餐厅（高德地图）：
      1. 坐标 WGS-84 → GCJ-02 转换；
      2. 用单一关键词（默认"美食"）按顺序翻页，让数量自然随 radius 变化；
      3. 按 "名称+地址" 去重，按评分降序；
      4. 最多返回 MAX_RESULTS 家。

    参数:
      - location: "纬度,经度"（内部会转换成 lng,lat 给高德）
      - radius: 搜索半径（米），100~50000
      - page_size: 1~25
      - query: 关键词（默认 美食）
    """
    key = _get_key()
    if not key:
        raise RuntimeError("未配置 AMAP_KEY，请到 .env 设置高德地图开放平台的 Key")

    # 1) 坐标转换：WGS-84 → GCJ-02
    location_str = None
    if location and "," in location:
        try:
            lat_s, lng_s = location.split(",")
            lat = float(lat_s.strip())
            lng = float(lng_s.strip())
            gcj_lat, gcj_lng = _wgs84_to_gcj02(lat, lng)
            # 高德要求 location = "lng,lat"
            location_str = f"{gcj_lng},{gcj_lat}"
        except (ValueError, TypeError):
            location_str = None

    if not location_str:
        raise RuntimeError("location 格式错误，必须是 \"纬度,经度\"，例如 39.915,116.404")

    # 2) 单一关键词按页码翻页，直到 API 返回未满一页或达到 safety_cap
    kw = (query or "美食").strip() or "美食"
    seen: Dict[str, Dict[str, Any]] = {}
    ps = max(10, min(25, page_size))  # 高德每页最大 25

    page_idx = 1
    while True:
        try:
            page = _fetch_one_page(
                key=key,
                keywords=kw,
                location_str=location_str,
                radius=radius,
                page_size=ps,
                page_num=page_idx,
            )
        except RuntimeError as e:
            if page_idx == 1:
                raise e
            break
        if not page:
            break
        for item in _parse_pois(page):
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
