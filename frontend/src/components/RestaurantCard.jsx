import React from 'react';

export default function RestaurantCard({ restaurant, onVote, compact = false }) {
  if (!restaurant) return null;

  return (
    <div className={`restaurant-card ${compact ? 'compact' : ''}`}>
      <div className="card-hero">
        <span className="card-emoji">{getEmoji(restaurant.name)}</span>
      </div>
      <div className="card-body">
        <h3 className="card-title">{restaurant.name}</h3>

        <div className="card-info-list">
          {restaurant.tags && (
            <div className="card-info-row">
              <span className="card-info-icon">🍴</span>
              <span>{restaurant.tags}</span>
            </div>
          )}
          {restaurant.rating && (
            <div className="card-info-row">
              <span>{Array.from({ length: restaurant.rating }).map(() => '⭐').join('')}</span>
              <span style={{ marginLeft: 6, color: '#777' }}>（{restaurant.rating} 分）</span>
            </div>
          )}
          {restaurant.address && (
            <div className="card-info-row">
              <span className="card-info-icon">📍</span>
              <span>{restaurant.address}</span>
            </div>
          )}
          {restaurant.price && restaurant.price > 0 && (
            <div className="card-info-row card-info-row--price">
              <span className="card-info-icon">💰</span>
              <span>人均 ¥{restaurant.price}</span>
            </div>
          )}
        </div>

        {onVote && (
          <button className="card-vote-btn" onClick={() => onVote(restaurant.id)}>
            👍 投它一票
          </button>
        )}
      </div>
    </div>
  );
}

const keywordEmoji = {
  鸡: '🍗',
  面: '🍜',
  寿司: '🍣',
  日本: '🍱',
  日式: '🍱',
  沙县: '🥟',
  披萨: '🍕',
  汉堡: '🍔',
  麦当劳: '🍟',
  肯德基: '🍗',
  烤肉: '🥩',
  火锅: '🍲',
  麻辣: '🌶️',
  意大: '🍝',
  咖: '☕',
  咖啡: '☕',
};

function getEmoji(name = '') {
  for (const key of Object.keys(keywordEmoji)) {
    if (name.includes(key)) return keywordEmoji[key];
  }
  return '🍽️';
}
