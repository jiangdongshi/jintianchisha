import { create } from 'zustand';
import { restaurantAPI, lotteryAPI, voteAPI } from '../api/client';

const genUserId = () => 'user_' + Math.random().toString(36).slice(2, 10);

export const useAppStore = create((set, get) => ({
  restaurants: [],
  result: null,
  isSpinning: false,
  history: [],
  topVoted: [],
  userId: localStorage.getItem('jtcs_user_id') || genUserId(),
  userName: localStorage.getItem('jtcs_user_name') || '我',
  error: null,

  init() {
    const id = get().userId;
    localStorage.setItem('jtcs_user_id', id);
  },

  setUserName(name) {
    localStorage.setItem('jtcs_user_name', name);
    set({ userName: name });
  },

  async fetchRestaurants() {
    try {
      const { data } = await restaurantAPI.list();
      set({ restaurants: data, error: null });
    } catch (e) {
      set({ error: '获取餐厅列表失败' });
    }
  },

  async draw() {
    const { restaurants, userId, userName } = get();
    if (restaurants.length === 0) {
      set({ error: '还没有餐厅，请先添加' });
      return null;
    }
    set({ isSpinning: true, result: null, error: null });
    try {
      const { data } = await lotteryAPI.draw(userId, userName);
      const target = restaurants.find((r) => r.id === data.restaurant.id) || data.restaurant;
      set({ result: { ...data, restaurant: target }, isSpinning: false });
      return target;
    } catch (e) {
      set({ isSpinning: false, error: '抽奖失败' });
      return null;
    }
  },

  async fetchHistory() {
    try {
      const { data } = await lotteryAPI.history();
      set({ history: data });
    } catch (e) {
      set({ error: '获取历史记录失败' });
    }
  },

  async vote(restaurantId) {
    const { userId, userName } = get();
    try {
      await voteAPI.create({ restaurant_id: restaurantId, user_id: userId, user_name: userName });
    } catch (e) {
      set({ error: '投票失败' });
    }
  },

  clearResult() {
    set({ result: null });
  },
}));
