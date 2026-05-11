import api from './axios';

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (email, password, full_name, role = 'user') => {
    const response = await api.post('/auth/register', { email, password, full_name, role });
    return response.data;
  },

  changePassword: async (old_password, new_password) => {
    const response = await api.post('/users/change-password', { old_password, new_password });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/users/me');
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

  repay: async (debt_id, data) => {
    const response = await api.post(`/debts/${debt_id}/repayments`, data);
    return response.data;
  },

  getRepayments: async (debt_id) => {
    const response = await api.get(`/debts/${debt_id}/repayments`);
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

  markActual: async (id) => {
    const response = await api.post(`/incomes/${id}/mark-actual`);
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
    const response = await api.get('/debts/repayments', { params });
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
    const response = await api.get('/analytics/debt-summary', { params });
    return response.data;
  },

  getDebtChange: async (params = {}) => {
    const response = await api.get('/analytics/debt-change', { params });
    return response.data;
  },

  getWeeklyBudget: async (params = {}) => {
    const response = await api.get('/analytics/weekly-budget', { params });
    return response.data;
  },

  getDailyBudget: async (params = {}) => {
    const response = await api.get('/analytics/daily-budget', { params });
    return response.data;
  },

  getBudgetSummary: async (params = {}) => {
    const response = await api.get('/analytics/budget-summary', { params });
    return response.data;
  },

  getDebtTimeline: async (params = {}) => {
    const response = await api.get('/analytics/debt-timeline', { params });
    return response.data;
  },

  getSeasonalDebt: async (params = {}) => {
    const response = await api.get('/analytics/seasonal-debt', { params });
    return response.data;
  },

  getYearlyDebt: async (params = {}) => {
    const response = await api.get('/analytics/yearly-debt', { params });
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

  getUrgentCreditCards: async () => {
    const response = await api.get('/analytics/urgent-credit-cards');
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

  deactivate: async (id) => {
    const response = await api.post(`/users/${id}/deactivate`);
    return response.data;
  },

  activate: async (id) => {
    const response = await api.post(`/users/${id}/activate`);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/users/${id}`);
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

export const debtHistoryService = {
  getAll: async () => {
    const response = await api.get('/debt-history');
    return response.data;
  },

  getByCreditor: async (creditorName) => {
    const response = await api.get(`/debt-history/${encodeURIComponent(creditorName)}`);
    return response.data;
  },
};

export const importService = {
  importExcel: async (formData) => {
    const response = await api.post('/imports/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  importExcelFull: async (formData) => {
    const response = await api.post('/imports/excel-full', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  resetData: async () => {
    const response = await api.post('/imports/excel-reset');
    return response.data;
  },
};

export const recordService = {
  getAll: async (params = {}) => {
    const response = await api.get('/records', { params });
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/records', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/records/${id}`, data);
    return response.data;
  },

  approve: async (id) => {
    const response = await api.post(`/records/${id}/approve`);
    return response.data;
  },

  reject: async (id) => {
    const response = await api.post(`/records/${id}/reject`);
    return response.data;
  },
};
