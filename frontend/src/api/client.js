import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 8000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('[API ERROR]', err?.message);
    return Promise.reject(err);
  }
);

export const restaurantAPI = {
  list: () => api.get('/restaurants/'),
  get: (id) => api.get(`/restaurants/${id}`),
  create: (data) => api.post('/restaurants/', data),
  update: (id, data) => api.put(`/restaurants/${id}`, data),
  remove: (id) => api.delete(`/restaurants/${id}`),
};

export const lotteryAPI = {
  draw: (userId, userName) =>
    api.post('/lottery/draw', null, {
      params: { winner_user_id: userId, winner_user_name: userName },
    }),
  history: () => api.get('/lottery/history'),
  drawNearby: (params) => api.post('/lottery/draw/nearby', null, { params }),
};

export const voteAPI = {
  create: (data) => api.post('/votes/', data),
  top: () => api.get('/votes/top'),
};

export const mapAPI = {
  import: (params) => api.post('/map/import', null, { params }),
};

export default api;
