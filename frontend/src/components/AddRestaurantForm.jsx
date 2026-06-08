import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';

export default function AddRestaurantForm() {
  const { fetchRestaurants } = useAppStore();
  const [form, setForm] = useState({
    name: '',
    description: '',
    address: '',
    phone: '',
    rating: 4,
    tags: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handle = (k) => (e) =>
    setForm({ ...form, [k]: k === 'rating' ? Number(e.target.value) : e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name) return;
    setSubmitting(true);
    try {
      await fetch('/api/restaurants/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      setForm({ name: '', description: '', address: '', phone: '', rating: 4, tags: '' });
      fetchRestaurants();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="add-form" onSubmit={submit}>
      <input
        placeholder="餐厅名称 *"
        value={form.name}
        onChange={handle('name')}
        required
      />
      <input
        placeholder="描述"
        value={form.description}
        onChange={handle('description')}
      />
      <input
        placeholder="地址"
        value={form.address}
        onChange={handle('address')}
      />
      <input
        placeholder="电话"
        value={form.phone}
        onChange={handle('phone')}
      />
      <input
        placeholder="标签，用逗号分隔（如：中餐,快炒,实惠）"
        value={form.tags}
        onChange={handle('tags')}
      />
      <label className="rating-row">
        评分：{form.rating} ⭐
        <input
          type="range"
          min="1"
          max="5"
          value={form.rating}
          onChange={handle('rating')}
        />
      </label>
      <button type="submit" disabled={submitting}>
        {submitting ? '添加中...' : '➕ 添加餐厅'}
      </button>
    </form>
  );
}
