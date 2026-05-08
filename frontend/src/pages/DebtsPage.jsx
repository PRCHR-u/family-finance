import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { debtService, analyticsService, creditorService } from '../api/services';

export default function DebtsPage() {
  const queryClient = useQueryClient();
  const { isAdmin } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [editingDebt, setEditingDebt] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [formData, setFormData] = useState({
    start_date: new Date().toISOString().split('T')[0],
    creditor_name: '',
    principal_amount: '',
    planned_payoff_date: '',
    interest_rate: '',
    comment: '',
  });

  const { data: debts, isLoading } = useQuery({
    queryKey: ['debts'],
    queryFn: () => debtService.getAll(),
  });

  const { data: creditors } = useQuery({
    queryKey: ['creditors'],
    queryFn: () => creditorService.getAll(),
  });

  const { data: weeklyBudget, isLoading: weeklyBudgetLoading } = useQuery({
    queryKey: ['weekly-budget'],
    queryFn: () => analyticsService.getWeeklyBudget({ weeks_ahead: 1 }),
  });

  const createMutation = useMutation({
    mutationFn: (data) => debtService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debts'] });
      queryClient.invalidateQueries({ queryKey: ['weekly-budget'] });
      setShowModal(false);
      resetForm();
      setErrorMessage('');
    },
    onError: (error) => setErrorMessage(error?.response?.data?.detail || 'Не удалось создать долг.'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => debtService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debts'] });
      queryClient.invalidateQueries({ queryKey: ['weekly-budget'] });
      setShowModal(false);
      setEditingDebt(null);
      resetForm();
      setErrorMessage('');
    },
    onError: (error) => setErrorMessage(error?.response?.data?.detail || 'Не удалось обновить долг.'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => debtService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debts'] });
      queryClient.invalidateQueries({ queryKey: ['weekly-budget'] });
      setErrorMessage('');
    },
    onError: (error) => setErrorMessage(error?.response?.data?.detail || 'Не удалось удалить долг.'),
  });

  const approveMutation = useMutation({
    mutationFn: (id) => debtService.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debts'] });
      queryClient.invalidateQueries({ queryKey: ['weekly-budget'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (id) => debtService.reject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debts'] });
      queryClient.invalidateQueries({ queryKey: ['weekly-budget'] });
    },
  });

  const resetForm = () => {
    setFormData({
      start_date: new Date().toISOString().split('T')[0],
      creditor_name: '',
      principal_amount: '',
      planned_payoff_date: '',
      interest_rate: '',
      comment: '',
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      creditor_name: formData.creditor_name,
      principal_amount: parseFloat(formData.principal_amount),
      start_date: formData.start_date,
      planned_payoff_date: formData.planned_payoff_date || null,
      interest_rate: formData.interest_rate ? parseFloat(formData.interest_rate) : null,
      comment: formData.comment || null,
    };

    if (editingDebt) {
      updateMutation.mutate({ id: editingDebt.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleEdit = (debt) => {
    setErrorMessage('');
    setEditingDebt(debt);
    setFormData({
      start_date: debt.start_date?.split('T')[0] || '',
      creditor_name: debt.creditor_name || '',
      principal_amount: debt.principal_amount?.toString() || '',
      planned_payoff_date: debt.planned_payoff_date?.split('T')[0] || '',
      interest_rate: debt.interest_rate?.toString() || '',
      comment: debt.comment || '',
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

  const pendingDebts = debts?.filter((d) => d.moderation_status === 'pending') || [];
  const approvedDebts = debts?.filter((d) => d.moderation_status === 'approved') || [];

  const debtTotal = useMemo(
    () => approvedDebts.reduce((sum, debt) => sum + (debt.current_balance || 0), 0),
    [approvedDebts]
  );

  const weeklySafeSpend = useMemo(() => {
    if (!weeklyBudget) return 0;
    const availableIncome = weeklyBudget.available_income || 0;
    const mandatory = weeklyBudget.mandatory_expenses?.total || 0;
    return Math.max(0, availableIncome - mandatory);
  }, [weeklyBudget]);

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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white shadow rounded-lg p-4">
          <p className="text-sm text-gray-600">Текущий долг (подтвержденный)</p>
          <p className="text-2xl font-semibold text-red-600">{debtTotal.toLocaleString('ru-RU')} ₽</p>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <p className="text-sm text-gray-600">Можно потратить за неделю</p>
          <p className="text-2xl font-semibold text-green-600">
            {weeklyBudgetLoading ? '...' : `${weeklySafeSpend.toLocaleString('ru-RU')} ₽`}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Лимит без роста долга = доходы за неделю - обязательные траты
          </p>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <p className="text-sm text-gray-600">Баланс недели</p>
          <p className={`text-2xl font-semibold ${(weeklyBudget?.balance || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {weeklyBudgetLoading ? '...' : `${(weeklyBudget?.balance || 0).toLocaleString('ru-RU')} ₽`}
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {errorMessage}
        </div>
      )}

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
                  <th className="px-4 py-2 text-right text-xs font-medium text-yellow-700 uppercase">Тело долга</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-yellow-700 uppercase">Остаток</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-yellow-700 uppercase">Описание</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-yellow-700 uppercase">Действия</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-yellow-200">
                {pendingDebts.map((debt) => (
                  <tr key={debt.id}>
                    <td className="px-4 py-2 text-sm text-gray-900">{new Date(debt.start_date).toLocaleDateString('ru-RU')}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{debt.creditor_name}</td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right">{debt.principal_amount?.toLocaleString('ru-RU')} ₽</td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right">{debt.current_balance?.toLocaleString('ru-RU')} ₽</td>
                    <td className="px-4 py-2 text-sm text-gray-600">{debt.comment || '—'}</td>
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
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Тело долга</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Остаток</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Комментарий</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Действия</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {approvedDebts.map((debt) => (
                  <tr key={debt.id}>
                    <td className="px-4 py-2 text-sm text-gray-900">{new Date(debt.start_date).toLocaleDateString('ru-RU')}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{debt.creditor_name}</td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right">{debt.principal_amount?.toLocaleString('ru-RU')} ₽</td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right">{debt.current_balance?.toLocaleString('ru-RU')} ₽</td>
                    <td className="px-4 py-2 text-sm text-gray-600">{debt.comment || '—'}</td>
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
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Кредитор</label>
                <select
                  required
                  value={formData.creditor_name}
                  onChange={(e) => setFormData({ ...formData, creditor_name: e.target.value })}
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
                  value={formData.principal_amount}
                  onChange={(e) => setFormData({ ...formData, principal_amount: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Плановая дата погашения</label>
                <input
                  type="date"
                  value={formData.planned_payoff_date}
                  onChange={(e) => setFormData({ ...formData, planned_payoff_date: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Ставка (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.interest_rate}
                  onChange={(e) => setFormData({ ...formData, interest_rate: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Комментарий</label>
                <textarea
                  rows="3"
                  value={formData.comment}
                  onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
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
                    setErrorMessage('');
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
