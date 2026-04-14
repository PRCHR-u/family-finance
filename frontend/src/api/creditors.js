import api from './axios';

export const creditorApi = {
  getAll: async () => {
    const response = await api.get('/creditors');
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/creditors', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/creditors/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/creditors/${id}`);
    return response.data;
  },
};
