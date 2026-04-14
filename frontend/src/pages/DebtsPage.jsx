import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { debtService } from '../api/services';
import { creditorService } from '../api/services';
import { Navigate } from 'react-router-dom';

export default function DebtsPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [editingDebt, setEditingDebt] = useState(null);
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    creditor: '',
    amount: '',
    description: '',
  });

  const { data: debts, isLoading } = useQuery({
    queryKey: ['debts'],
    queryFn: () => debtService.getAll(),
  });

  const { data: creditors } = useQuery({
    queryKey: ['creditors'],
    queryFn: () => creditorService.getAll(),
  });

  const createMutation = useMutation({
    mutationFn: (data) => debtService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['debts']);
      setShowModal(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => debtService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['debts']);
      setShowModal(false);
      setEditingDebt(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => debtService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['debts']);
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id) => debtService.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['debts']);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (id) => debtService.reject(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['debts']);
    },
  });

  const resetForm = () => {
    setFormData({
      date: new Date().toISOString().split('T')[0],
      creditor: '',
      amount: '',
      description: '',
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      amount: parseFloat(formData.amount),
    };

    if (editingDebt) {
      updateMutation.mutate({ id: editingDebt.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleEdit = (debt) => {
    setEditingDebt(debt);
    setFormData({
      date: debt.date.split('T')[0],
      creditor: debt.creditor,
      amount: debt.amount.toString(),
      description: debt.description || '',
    });
    setShowModal(true);
  };

  const handleDelete = (id) => {
    if (confirm('Вы уверены, что хотите удалить эту запись?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleApprove = (id) => {
    approveMutation.mutate(id);
  };

  const handleReject = (id) => {
    rejectMutation.mutate(id);
  };

  const pendingDebts = debts?.filter(d => !d.is_approved) || [];
  const approvedDebts = debts?.filter(d => d.is_approved) || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Долги</h1>
        <button
          onClick={() => {
            resetForm();
            setEditingDebt(null);
            setShowModal(true);
          }}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          Добавить долг
        </button>
      </div>

      {/* Pending Debts */}
      {isAdmin && pendingDebts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-yellow-100 border-b border-yellow-200">
            <h2 className="text-lg font-medium text-yellow-800">На модерации ({pendingDebts.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-yellow-200">
              <thead className="bg-yellow-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-yellow-700 uppercase">Дата</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-yellow-700 uppercase">Кредитор</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-yellow-700 uppercase">Сумма</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-yellow-700 uppercase">Описание</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-yellow-700 uppercase">Действия</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-yellow-200">
                {pendingDebts.map((debt) => (
                  <tr key={debt.id}>
                    <td className="px-4 py-2 text-sm text-gray-900">{new Date(debt.date).toLocaleDateString('ru-RU')}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{debt.creditor}</td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right">{debt.amount?.toLocaleString('ru-RU')} ₽</td>
                    <td className="px-4 py-2 text-sm text-gray-600">{debt.description}</td>
                    <td className="px-4 py-2 text-center space-x-2">
                      <button
                        onClick={() => handleApprove(debt.id)}
                        className="text-green-600 hover:text-green-800 text-sm font-medium"
                      >
                        ✓
                      </button>
                      <button
                        onClick={() => handleReject(debt.id)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        ✗
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Approved Debts */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Подтвержденные долги ({approvedDebts.length})</h2>
        </div>
        {isLoading ? (
          <div className="text-center py-8">Загрузка...</div>
        ) : approvedDebts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">Нет записей</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Дата</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Кредитор</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Сумма</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Описание</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Действия</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {approvedDebts.map((debt) => (
                  <tr key={debt.id}>
                    <td className="px-4 py-2 text-sm text-gray-900">{new Date(debt.date).toLocaleDateString('ru-RU')}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{debt.creditor}</td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right">{debt.amount?.toLocaleString('ru-RU')} ₽</td>
                    <td className="px-4 py-2 text-sm text-gray-600">{debt.description}</td>
                    <td className="px-4 py-2 text-center space-x-2">
                      <button
                        onClick={() => handleEdit(debt)}
                        className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                      >
                        ✎
                      </button>
                      <button
                        onClick={() => handleDelete(debt.id)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        🗑
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingDebt ? 'Редактировать долг' : 'Новый долг'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Дата</label>
                <input
                  type="date"
                  required
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Кредитор</label>
                <select
                  required
                  value={formData.creditor}
                  onChange={(e) => setFormData({ ...formData, creditor: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Выберите кредитора</option>
                  {creditors?.map((c) => (
                    <option key={c.id} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Сумма (₽)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Описание</label>
                <textarea
                  rows="3"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingDebt(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {createMutation.isPending || updateMutation.isPending ? 'Сохранение...' : 'Сохранить'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function PrivateRoute({ children, adminOnly = false }) {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  if (adminOnly && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
}
