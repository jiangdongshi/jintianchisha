import React, { useEffect, useState, useRef } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { useAppStore } from './store/useAppStore';
import { mapAPI } from './api/client';
import WheelSpinner from './components/WheelSpinner';
import RestaurantCard from './components/RestaurantCard';
import ResultModal from './components/ResultModal';
import MapImport from './components/MapImport';

// --- 工具函数 ---
// Haversine 公式，米
function haversineM(lat1, lng1, lat2, lng2) {
  const R = 6371000.0;
  const toRad = (v) => (v * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function pickRandom(arr) {
  if (!arr || arr.length === 0) return null;
  return arr[Math.floor(Math.random() * arr.length)];
}

const presetRadii = [
  { label: '步行 5 分钟 (400m)', value: 400 },
  { label: '步行 10 分钟 (800m)', value: 800 },
  { label: '步行 20 分钟 (1500m)', value: 1500 },
  { label: '打车 10 分钟 (5km)', value: 5000 },
];

function HomePage() {
  const { restaurants, fetchRestaurants } = useAppStore();

  const [coords, setCoords] = useState(null);
  const [locError, setLocError] = useState('');
  const [locLoading, setLocLoading] = useState(false);

  const [radiusMeters, setRadiusMeters] = useState(500); // 默认 500m
  const [minBudget, setMinBudget] = useState('');
  const [maxBudget, setMaxBudget] = useState('');

  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [rawCandidates, setRawCandidates] = useState([]); // 地图返回的原始列表（不过滤）
  const [candidates, setCandidates] = useState([]); // 应用预算过滤后的列表
  const [pick, setPick] = useState(null);

  // 预算过滤（纯客户端，不请求后端）
  const applyBudgetFilter = (items) => {
    const minB = minBudget === '' || minBudget === null ? null : Number(minBudget);
    const maxB = maxBudget === '' || maxBudget === null ? null : Number(maxBudget);
    if (minB === null && maxB === null) return items;
    return items.filter((it) => {
      if (it.price === null || it.price <= 0) return false;
      if (minB !== null && it.price < minB) return false;
      if (maxB !== null && it.price > maxB) return false;
      return true;
    });
  };

  // 防抖改半径（避免滑块拖动时频繁请求）
  const radiusTimerRef = useRef(null);

  // ① 自动定位
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocError('当前浏览器不支持定位');
      return;
    }
    setLocLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocLoading(false);
      },
      (err) => {
        setLocError('定位被拒绝了：' + err.message + '，可点击下面的「手动定位」按钮重新请求');
        setLocLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);

  // 手动定位
  const requestLoc = () => {
    if (!navigator.geolocation) return;
    setLocLoading(true);
    setLocError('');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocLoading(false);
      },
      (err) => {
        setLocError('定位失败：' + err.message);
        setLocLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // ② 搜索附近餐厅
  const doSearch = async (lat, lng, radius) => {
    if (!lat || !lng) return;
    setSearchLoading(true);
    setSearchError('');
    setPick(null);
    try {
      const locationStr = `${lat},${lng}`;
      const { data } = await mapAPI.import({
        location: locationStr,
        radius,
        page_size: 20,
        page_num: 0,
        query: '美食',
        save: true,
      });
      const items = (data.items || []).map((it) => ({
        name: it.name,
        address: it.address || '',
        rating: it.rating || null,
        price: it.price ? Number(it.price) : null,
        tags: it.tags || '',
        latitude: it.latitude,
        longitude: it.longitude,
      }));
      setRawCandidates(items);
      setCandidates(applyBudgetFilter(items)); // 应用预算过滤
      fetchRestaurants();
    } catch (e) {
      const msg = e?.response?.data?.detail || e.message || '搜索失败';
      setSearchError(msg);
      setRawCandidates([]);
      setCandidates([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // ③ 定位成功 + 半径变化 → 自动刷新
  useEffect(() => {
    if (!coords) return;
    if (radiusTimerRef.current) clearTimeout(radiusTimerRef.current);
    radiusTimerRef.current = setTimeout(() => {
      doSearch(coords.lat, coords.lng, radiusMeters);
    }, 200);
    return () => {
      if (radiusTimerRef.current) clearTimeout(radiusTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [coords, radiusMeters]);

  // ④ 预算变化 → 纯客户端重新过滤（不请求地图API，省配额）
  useEffect(() => {
    setPick(null);
    setCandidates(applyBudgetFilter(rawCandidates));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minBudget, maxBudget]);

  // ⑤ 手动刷新按钮
  const onRefresh = () => {
    if (coords) doSearch(coords.lat, coords.lng, radiusMeters);
  };

  // ⑥ 抽签
  const onDraw = () => {
    if (!candidates || candidates.length === 0) {
      alert('还没搜到附近的餐厅，稍等一下～');
      return;
    }
    const r = pickRandom(candidates);
    if (!r) return;
    const distance =
      coords && r.latitude && r.longitude
        ? haversineM(coords.lat, coords.lng, Number(r.latitude), Number(r.longitude))
        : 0;
    setPick({
      restaurant: r,
      distance_km: +(distance / 1000).toFixed(2),
      walk_min: Math.max(1, Math.round(distance / 80)),
      drive_min: Math.max(1, Math.round(distance / 450)),
      pool_size: candidates.length,
    });
  };

  const budgetHint = () => {
    const a = minBudget === '' || minBudget === null ? null : Number(minBudget);
    const b = maxBudget === '' || maxBudget === null ? null : Number(maxBudget);
    if (a !== null && b !== null) return `预算 ¥${a}-${b}`;
    if (a !== null) return `预算 ≥ ¥${a}`;
    if (b !== null) return `预算 ≤ ¥${b}`;
    return '';
  };

  return (
    <div className="page home-page">
      <div className="hero">
        <h1>📍 今天吃啥？</h1>
        <p className="hero-sub">
          {locLoading
            ? '正在定位...'
            : coords
            ? '已定位，选个距离就开抽！'
            : locError
            ? '定位失败，点右上角手动定位'
            : '正在定位...'}
        </p>
      </div>

      <div className="loc-panel">
        <div className="loc-info">
          {locLoading && <span>⏳ 正在定位...</span>}
          {!locLoading && coords && (
            <span>✅ 已定位：{coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}</span>
          )}
          {!locLoading && !coords && locError && <span className="loc-warn">⚠️ {locError}</span>}
        </div>
        {coords === null && (
          <button className="mini-btn" onClick={requestLoc}>手动定位</button>
        )}
      </div>

      {/* 主卡片：预算 + 范围 + 候选 + 抽签 */}
      <div className="filter-panel">

        <label className="block-label">
          人均预算（元，可不填）
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <input
              value={minBudget}
              onChange={(e) => setMinBudget(e.target.value.replace(/[^\d]/g, ''))}
              placeholder="最低，如 30"
              style={{ flex: 1 }}
            />
            <span style={{ alignSelf: 'center', color: '#999' }}>—</span>
            <input
              value={maxBudget}
              onChange={(e) => setMaxBudget(e.target.value.replace(/[^\d]/g, ''))}
              placeholder="最高，如 200"
              style={{ flex: 1 }}
            />
          </div>
        </label>

        <div className="chips-row">
          {presetRadii.map((r) => (
            <button
              key={r.value}
              className={'radius-chip ' + (radiusMeters === r.value ? 'active' : '')}
              onClick={() => setRadiusMeters(r.value)}
            >
              {r.label}
            </button>
          ))}
        </div>

        <div>
          <input
            type="range"
            min={200}
            max={15000}
            step={100}
            value={radiusMeters}
            onChange={(e) => setRadiusMeters(Number(e.target.value))}
          />
          <div className="slider-value">搜索范围：{Math.round(radiusMeters)} 米（约 {Math.round(radiusMeters / 80)} 分钟步行）</div>
        </div>

        {/* 候选池状态 */}
        <div className="pool-state">
          {searchLoading && <span>🌀 正在搜附近餐厅...</span>}
          {!searchLoading && searchError && (
            <span className="loc-warn">⚠️ {searchError}</span>
          )}
          {!searchLoading && !searchError && (
            <span>
              ✅ 附近共 <b>{candidates.length}</b> 家
              {budgetHint() ? ` · ${budgetHint()}` : ''}
            </span>
          )}
        </div>

        <button
          className="btn-big"
          onClick={onDraw}
          disabled={!coords || candidates.length === 0 || searchLoading}
        >
          {!coords
            ? '📍 请先允许浏览器定位'
            : searchLoading
            ? '🌀 正在搜索...'
            : candidates.length === 0
            ? '附近没搜到餐厅，试试放大范围'
            : '🎯 开始抽签！'}
        </button>

        <button className="btn-secondary" onClick={onRefresh} disabled={!coords || searchLoading}>
          🔄 刷新附近餐厅
        </button>
      </div>

      {/* 结果卡片 */}
      {pick && (
        <div className="result-card">
          <div className="modal-confetti">🎉</div>
          <h2 className="modal-title">{pick.restaurant.name}</h2>
          <p className="result-address">📍 {pick.restaurant.address}</p>

          <div className="result-info">
            {pick.restaurant.tags && <div className="result-info-row">🍴 {pick.restaurant.tags}</div>}
            {pick.restaurant.rating && (
              <div className="result-info-row">
                {Array.from({ length: pick.restaurant.rating }).map(() => '⭐').join('')}（{pick.restaurant.rating} 分）
              </div>
            )}
            {pick.restaurant.price && pick.restaurant.price > 0 && (
              <div className="result-info-row result-info-row--price">
                💰 人均 ¥{pick.restaurant.price}
              </div>
            )}
          </div>

          <div className="distance-info">
            <span>🚶 步行 ~{pick.walk_min} 分钟</span>
            <span>🚕 打车 ~{pick.drive_min} 分钟</span>
            <span>📏 {pick.distance_km} km</span>
          </div>
          <p className="pool-info">从 {pick.pool_size} 家候选里抽出</p>
          <button className="btn-primary" onClick={onDraw}>再来一次</button>
        </div>
      )}

      <div style={{ height: 24 }} />
    </div>
  );
}

function RestaurantsPage() {
  const { restaurants, fetchRestaurants, vote } = useAppStore();

  useEffect(() => {
    fetchRestaurants();
  }, []);

  return (
    <div className="page list-page">
      <header className="sub-header">
        <Link to="/" className="back-link">← 返回</Link>
        <h2>📋 餐厅列表</h2>
      </header>

      <MapImport onDone={fetchRestaurants} />

      <div className="grid">
        {restaurants.map((r) => (
          <RestaurantCard key={r.id} restaurant={r} onVote={vote} />
        ))}
      </div>

      {restaurants.length === 0 && (
        <p className="empty-tip">还没有餐厅，从地图导入附近餐厅试试 →</p>
      )}
    </div>
  );
}

function NavBar() {
  const loc = useLocation();
  return (
    <nav className="nav">
      <Link className={loc.pathname === '/' ? 'active' : ''} to="/">🎲 抽签</Link>
      <Link className={loc.pathname === '/restaurants' ? 'active' : ''} to="/restaurants">📋 餐厅</Link>
      <span className="nav-brand">🍜 今天吃啥</span>
    </nav>
  );
}

export default function App() {
  return (
    <div className="app-root">
      <NavBar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/restaurants" element={<RestaurantsPage />} />
      </Routes>
      <footer className="app-footer">· Made with ❤️ by 今天吃啥团队 ·</footer>
    </div>
  );
}
