import api from './axios';

export const expenseApi = {
  getAll: async (params = {}) => {
    const response = await api.get('/expenses', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/expenses/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/expenses', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/expenses/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/expenses/${id}`);
    return response.data;
  },

  complete: async (id) => {
    const response = await api.post(`/expenses/${id}/complete`);
    return response.data;
  },

  approve: async (id) => {
    const response = await api.post(`/expenses/${id}/approve`);
    return response.data;
  },

  reject: async (id) => {
    const response = await api.post(`/expenses/${id}/reject`);
    return response.data;
  },
};
