import React, { useState } from 'react';
import { mapAPI } from '../api/client';

export default function MapImport({ onDone }) {
  const [mode, setMode] = useState('location'); // 'region' or 'location'
  const [query, setQuery] = useState('美食');
  const [region, setRegion] = useState('北京');
  const [lat, setLat] = useState('');
  const [lng, setLng] = useState('');
  const [radius, setRadius] = useState(1000);
  const [save, setSave] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setError('浏览器不支持定位');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLng(pos.coords.longitude.toFixed(6));
        setMode('location');
        setError('');
      },
      (err) => setError('定位失败：' + err.message)
    );
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const params = { query, radius, save };
      if (mode === 'location') {
        if (!lat || !lng) {
          throw new Error('请填写经纬度，或点击「使用我的位置」');
        }
        params.location = `${lat},${lng}`;
      } else {
        params.region = region;
      }
      const { data } = await mapAPI.import(params);
      setResult(data);
      if (onDone) onDone();
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || '导入失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="map-import-card">
      <h3 style={{ marginTop: 0 }}>🗺️ 从地图导入附近餐厅</h3>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <label style={{ cursor: 'pointer' }}>
          <input
            type="radio"
            checked={mode === 'region'}
            onChange={() => setMode('region')}
          />{' '}
          按城市搜索
        </label>
        <label style={{ cursor: 'pointer' }}>
          <input
            type="radio"
            checked={mode === 'location'}
            onChange={() => setMode('location')}
          />{' '}
          按坐标搜附近
        </label>
      </div>

      <form onSubmit={submit} className="map-form">
        <label>
          关键词
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="美食/火锅/日料" />
        </label>

        {mode === 'region' ? (
          <label>
            城市
            <input value={region} onChange={(e) => setRegion(e.target.value)} placeholder="如：北京" />
          </label>
        ) : (
          <div className="latlng-row">
            <label>
              纬度
              <input value={lat} onChange={(e) => setLat(e.target.value)} placeholder="如 39.915" />
            </label>
            <label>
              经度
              <input value={lng} onChange={(e) => setLng(e.target.value)} placeholder="如 116.404" />
            </label>
            <button type="button" onClick={handleUseMyLocation} className="mini-btn">
              📍 使用我的位置
            </button>
          </div>
        )}

        <label>
          半径（米）：{radius}
          <input type="range" min="100" max="20000" step="100" value={radius}
                 onChange={(e) => setRadius(Number(e.target.value))} />
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <input type="checkbox" checked={save} onChange={(e) => setSave(e.target.checked)} />
          同时保存到数据库
        </label>

        <button type="submit" disabled={loading} className="btn-primary" style={{ padding: '10px' }}>
          {loading ? '搜索中...' : '🔍 从地图搜索'}
        </button>
      </form>

      {error && <div style={{ color: '#c62828', marginTop: 12 }}>⚠️ {error}</div>}

      {result && (
        <div className="map-result">
          <div className="map-result-summary">
            找到 <b>{result.count}</b> 家
            {save && <>，已保存 <b style={{ color: '#ff5a36' }}>{result.saved}</b> 家到数据库</>}
          </div>

          <ul className="map-result-list">
            {(result.items || []).slice(0, 10).map((r, i) => (
              <li key={i}>
                <div className="map-item-name">🍱 {r.name}</div>
                <div className="map-item-info">
                  {r.tags && <div className="map-item-row">🍴 {r.tags}</div>}
                  {r.rating && (
                    <div className="map-item-row">
                      {Array.from({ length: r.rating }).map(() => '⭐').join('')}（{r.rating} 分）
                    </div>
                  )}
                  {r.address && <div className="map-item-row">📍 {r.address}</div>}
                  {r.price && r.price > 0 && (
                    <div className="map-item-row map-item-row--price">💰 人均 ¥{r.price}</div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
