import React, { useEffect, useState } from 'react';

export default function WheelSpinner({ restaurants, targetRestaurant, isSpinning, onStop }) {
  const [displayIndex, setDisplayIndex] = useState(0);
  const [speed, setSpeed] = useState(80);

  useEffect(() => {
    if (!isSpinning || restaurants.length === 0) return;

    setSpeed(80);
    let current = 0;
    let currentSpeed = 80;

    const runTick = () => {
      current = (current + 1) % restaurants.length;
      setDisplayIndex(current);

      if (currentSpeed >= 400) {
        const targetIndex = restaurants.findIndex((r) => r.id === targetRestaurant?.id);
        if (targetIndex !== -1) {
          setDisplayIndex(targetIndex);
        }
        setTimeout(() => onStop && onStop(), 400);
        return;
      }

      currentSpeed += 15;
      setSpeed(currentSpeed);
      setTimeout(runTick, currentSpeed);
    };

    setTimeout(runTick, 100);
  }, [isSpinning, restaurants, targetRestaurant]);

  if (restaurants.length === 0) {
    return <div className="spinner-empty">🍽️ 暂无餐厅</div>;
  }

  const current = restaurants[displayIndex];

  return (
    <div className={`wheel-spinner ${isSpinning ? 'spinning' : ''}`}>
      <div className="wheel-frame">
        <div className="wheel-pointer">⬇️</div>
        <div className="wheel-display" style={{ transitionDuration: `${speed}ms` }}>
          <div className="wheel-emoji">🍱</div>
          <div className="wheel-name">{current?.name || '?'}</div>
          <div className="wheel-rating">
            {current?.rating
              ? Array.from({ length: current.rating }).map((_, i) => <span key={i}>⭐</span>)
              : '—'}
          </div>
        </div>
        {isSpinning && <div className="wheel-shine"></div>}
      </div>
    </div>
  );
}
