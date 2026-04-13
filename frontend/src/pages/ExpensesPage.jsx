import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { expenseApi } from '../api/expenses';
import { creditorApi } from '../api/creditors';

const ExpensesPage = () => {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all'); // all, pending, completed, rejected
  const [formData, setFormData] = useState({
    amount: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    creditor_id: '',
    category: 'utilities',
    is_completed: false,
    is_planned: false
  });

  const { data: expenses, isLoading } = useQuery({
    queryKey: ['expenses'],
    queryFn: expenseApi.getAll
  });

  const { data: creditors } = useQuery({
    queryKey: ['creditors'],
    queryFn: creditorApi.getAll
  });

  const createMutation = useMutation({
    mutationFn: expenseApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['expenses']);
      setShowModal(false);
      resetForm();
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => expenseApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['expenses']);
      setShowModal(false);
      setEditingExpense(null);
      resetForm();
    }
  });

  const deleteMutation = useMutation({
    mutationFn: expenseApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['expenses']);
    }
  });

  const completeMutation = useMutation({
    mutationFn: expenseApi.complete,
    onSuccess: () => {
      queryClient.invalidateQueries(['expenses']);
    }
  });

  const rejectMutation = useMutation({
    mutationFn: expenseApi.reject,
    onSuccess: () => {
      queryClient.invalidateQueries(['expenses']);
    }
  });

  const isAdmin = localStorage.getItem('role') === 'admin';

  const resetForm = () => {
    setFormData({
      amount: '',
      description: '',
      date: new Date().toISOString().split('T')[0],
      creditor_id: '',
      category: 'utilities',
      is_completed: false,
      is_planned: false
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      ...formData,
      amount: parseFloat(formData.amount)
    };

    if (editingExpense) {
      updateMutation.mutate({ id: editingExpense.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleEdit = (expense) => {
    setEditingExpense(expense);
    setFormData({
      amount: expense.amount.toString(),
      description: expense.description,
      date: expense.date.split('T')[0],
      creditor_id: expense.creditor_id || '',
      category: expense.category,
      is_completed: expense.is_completed,
      is_planned: expense.is_planned
    });
    setShowModal(true);
  };

  const handleDelete = (id) => {
    if (window.confirm('Вы уверены, что хотите удалить эту запись?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleComplete = (id) => {
    completeMutation.mutate(id);
  };

  const handleReject = (id) => {
    rejectMutation.mutate(id);
  };

  const filteredExpenses = expenses?.filter(expense => {
    if (filterStatus === 'all') return true;
    if (filterStatus === 'pending') return !expense.is_completed && expense.status === 'pending';
    if (filterStatus === 'completed') return expense.is_completed;
    if (filterStatus === 'rejected') return expense.status === 'rejected';
    return true;
  });

  if (isLoading) return <div className="p-4">Загрузка...</div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Расходы</h1>
        <button
          onClick={() => {
            setEditingExpense(null);
            resetForm();
            setShowModal(true);
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          + Добавить расход
        </button>
      </div>

      {/* Фильтры */}
      <div className="mb-4 flex gap-2">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2"
        >
          <option value="all">Все</option>
          <option value="pending">На модерации</option>
          <option value="completed">Выполненные</option>
          <option value="rejected">Отклоненные</option>
        </select>
      </div>

      {/* Таблица */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Дата</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Сумма</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Описание</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Категория</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Кредитор</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredExpenses?.map((expense) => (
              <tr key={expense.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(expense.date).toLocaleDateString('ru-RU')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {expense.amount.toFixed(2)} ₽
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">{expense.description}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {expense.category === 'utilities' ? 'Коммуналка' :
                   expense.category === 'rent' ? 'Аренда' :
                   expense.category === 'food' ? 'Еда' :
                   expense.category === 'transport' ? 'Транспорт' :
                   expense.category === 'entertainment' ? 'Развлечения' :
                   expense.category === 'other'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {expense.creditor_name || '—'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    expense.is_completed ? 'bg-green-100 text-green-800' :
                    expense.status === 'rejected' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {expense.is_completed ? 'Выполнен' :
                     expense.status === 'rejected' ? 'Отклонен' :
                     'На модерации'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => handleEdit(expense)}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    ✏️
                  </button>
                  {isAdmin && !expense.is_completed && expense.status !== 'rejected' && (
                    <>
                      <button
                        onClick={() => handleComplete(expense.id)}
                        className="text-green-600 hover:text-green-900 mr-3"
                        title="Подтвердить"
                      >
                        ✓
                      </button>
                      <button
                        onClick={() => handleReject(expense.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Отклонить"
                      >
                        ✗
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => handleDelete(expense.id)}
                    className="text-red-600 hover:text-red-900 ml-3"
                  >
                    🗑️
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Модальное окно */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingExpense ? 'Редактировать расход' : 'Новый расход'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Сумма</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.amount}
                  onChange={(e) => setFormData({...formData, amount: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
                <input
                  type="text"
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Дата</label>
                <input
                  type="date"
                  required
                  value={formData.date}
                  onChange={(e) => setFormData({...formData, date: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Категория</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="utilities">Коммуналка</option>
                  <option value="rent">Аренда</option>
                  <option value="food">Еда</option>
                  <option value="transport">Транспорт</option>
                  <option value="entertainment">Развлечения</option>
                  <option value="other">Другое</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Кредитор (опционально)</label>
                <select
                  value={formData.creditor_id}
                  onChange={(e) => setFormData({...formData, creditor_id: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="">Не выбрано</option>
                  {creditors?.map(creditor => (
                    <option key={creditor.id} value={creditor.id}>
                      {creditor.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_planned}
                    onChange={(e) => setFormData({...formData, is_planned: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Планируемый расход</span>
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
};

export default ExpensesPage;
