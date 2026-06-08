import React from 'react';
import RestaurantCard from './RestaurantCard';

export default function ResultModal({ result, onClose, onRedraw, onVote }) {
  if (!result) return null;

  return (
    <div className="modal-mask" onClick={onClose}>
      <div className="modal-body" onClick={(e) => e.stopPropagation()}>
        <div className="modal-confetti">🎉 🎊 🏆 🎉 🎊</div>
        <h2 className="modal-title">今天就吃它啦！</h2>
        <RestaurantCard restaurant={result.restaurant} onVote={onVote} />
        <div className="modal-time">
          抽奖时间：{new Date(result.lottery_time).toLocaleString('zh-CN')}
        </div>
        <div className="modal-actions">
          <button className="btn-primary" onClick={onRedraw}>
            🎲 再来一次
          </button>
          <button className="btn-ghost" onClick={onClose}>
            就决定是它了
          </button>
        </div>
      </div>
    </div>
  );
}
