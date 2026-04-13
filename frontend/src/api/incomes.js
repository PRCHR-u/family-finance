import api from './axios';

export const incomeApi = {
  getAll: async (params = {}) => {
    const response = await api.get('/incomes', { params });
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/incomes', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/incomes/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/incomes/${id}`);
    return response.data;
  },

  approve: async (id) => {
    const response = await api.post(`/incomes/${id}/approve`);
    return response.data;
  },

  reject: async (id) => {
    const response = await api.post(`/incomes/${id}/reject`);
    return response.data;
  },
};
