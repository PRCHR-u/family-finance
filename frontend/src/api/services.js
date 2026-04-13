import api from './axios';

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (email, password, full_name) => {
    const response = await api.post('/auth/register', { email, password, full_name });
    return response.data;
  },

  changePassword: async (old_password, new_password) => {
    const response = await api.post('/auth/change-password', { old_password, new_password });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

export const debtService = {
  getAll: async (params = {}) => {
    const response = await api.get('/debts', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/debts/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/debts', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/debts/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/debts/${id}`);
    return response.data;
  },

  approve: async (id) => {
    const response = await api.post(`/debts/${id}/approve`);
    return response.data;
  },

  reject: async (id) => {
    const response = await api.post(`/debts/${id}/reject`);
    return response.data;
  },
};

export const expenseService = {
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

  markComplete: async (id) => {
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

export const incomeService = {
  getAll: async (params = {}) => {
    const response = await api.get('/incomes', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/incomes/${id}`);
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

export const creditCardService = {
  getAll: async (params = {}) => {
    const response = await api.get('/credit-cards', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/credit-cards/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/credit-cards', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/credit-cards/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/credit-cards/${id}`);
    return response.data;
  },

  approve: async (id) => {
    const response = await api.post(`/credit-cards/${id}/approve`);
    return response.data;
  },

  reject: async (id) => {
    const response = await api.post(`/credit-cards/${id}/reject`);
    return response.data;
  },
};

export const repaymentService = {
  getAll: async (params = {}) => {
    const response = await api.get('/repayments', { params });
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/repayments', data);
    return response.data;
  },

  approve: async (id) => {
    const response = await api.post(`/repayments/${id}/approve`);
    return response.data;
  },

  reject: async (id) => {
    const response = await api.post(`/repayments/${id}/reject`);
    return response.data;
  },
};

export const analyticsService = {
  getDebtAnalytics: async (params = {}) => {
    const response = await api.get('/analytics/debt', { params });
    return response.data;
  },

  getBudgetAnalytics: async (params = {}) => {
    const response = await api.get('/analytics/budget', { params });
    return response.data;
  },

  getFinancialHealth: async () => {
    const response = await api.get('/analytics/financial-health');
    return response.data;
  },

  exportData: async () => {
    const response = await api.get('/analytics/export', { responseType: 'blob' });
    return response.data;
  },
};

export const auditLogService = {
  getAll: async (params = {}) => {
    const response = await api.get('/audit-logs', { params });
    return response.data;
  },

  export: async () => {
    const response = await api.get('/audit-logs/export', { responseType: 'blob' });
    return response.data;
  },
};

export const userService = {
  getAll: async (params = {}) => {
    const response = await api.get('/users', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/users/${id}`, data);
    return response.data;
  },

  toggleActive: async (id) => {
    const response = await api.post(`/users/${id}/toggle-active`);
    return response.data;
  },

  setRole: async (id, role) => {
    const response = await api.post(`/users/${id}/set-role`, { role });
    return response.data;
  },
};

export const creditorService = {
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

export const creditCardIssuerService = {
  getAll: async () => {
    const response = await api.get('/credit-card-issuers');
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/credit-card-issuers', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/credit-card-issuers/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/credit-card-issuers/${id}`);
    return response.data;
  },
};
