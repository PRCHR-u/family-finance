import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { incomeApi } from '../api/incomes';

const IncomesPage = () => {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editingIncome, setEditingIncome] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [formData, setFormData] = useState({
    amount: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    category: 'salary',
    is_planned: false
  });

  const { data: incomes, isLoading } = useQuery({
    queryKey: ['incomes'],
    queryFn: incomeApi.getAll
  });

  const createMutation = useMutation({
    mutationFn: incomeApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['incomes']);
      setShowModal(false);
      resetForm();
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => incomeApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['incomes']);
      setShowModal(false);
      setEditingIncome(null);
      resetForm();
    }
  });

  const deleteMutation = useMutation({
    mutationFn: incomeApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['incomes']);
    }
  });

  const approveMutation = useMutation({
    mutationFn: incomeApi.approve,
    onSuccess: () => {
      queryClient.invalidateQueries(['incomes']);
    }
  });

  const rejectMutation = useMutation({
    mutationFn: incomeApi.reject,
    onSuccess: () => {
      queryClient.invalidateQueries(['incomes']);
    }
  });

  const isAdmin = localStorage.getItem('role') === 'admin';

  const resetForm = () => {
    setFormData({
      amount: '',
      description: '',
      date: new Date().toISOString().split('T')[0],
      category: 'salary',
      is_planned: false
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      ...formData,
      amount: parseFloat(formData.amount)
    };

    if (editingIncome) {
      updateMutation.mutate({ id: editingIncome.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleEdit = (income) => {
    setEditingIncome(income);
    setFormData({
      amount: income.amount.toString(),
      description: income.description,
      date: income.date.split('T')[0],
      category: income.category,
      is_planned: income.is_planned
    });
    setShowModal(true);
  };

  const handleDelete = (id) => {
    if (window.confirm('Вы уверены, что хотите удалить эту запись?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleApprove = (id) => {
    approveMutation.mutate(id);
  };

  const handleReject = (id) => {
    rejectMutation.mutate(id);
  };

  const filteredIncomes = incomes?.filter(income => {
    if (filterStatus === 'all') return true;
    if (filterStatus === 'pending') return income.status === 'pending';
    if (filterStatus === 'approved') return income.status === 'approved';
    if (filterStatus === 'rejected') return income.status === 'rejected';
    return true;
  });

  if (isLoading) return <div className="p-4">Загрузка...</div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Доходы</h1>
        <button
          onClick={() => {
            setEditingIncome(null);
            resetForm();
            setShowModal(true);
          }}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
        >
          + Добавить доход
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
          <option value="approved">Подтвержденные</option>
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
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Тип</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredIncomes?.map((income) => (
              <tr key={income.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(income.date).toLocaleDateString('ru-RU')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {income.amount.toFixed(2)} ₽
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">{income.description}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {income.category === 'salary' ? 'Зарплата' :
                   income.category === 'bonus' ? 'Премия' :
                   income.category === 'investment' ? 'Инвестиции' :
                   income.category === 'gift' ? 'Подарок' :
                   income.category === 'other'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {income.is_planned ? 'Планируемый' : 'Фактический'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    income.status === 'approved' ? 'bg-green-100 text-green-800' :
                    income.status === 'rejected' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {income.status === 'approved' ? 'Подтвержден' :
                     income.status === 'rejected' ? 'Отклонен' :
                     'На модерации'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => handleEdit(income)}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    ✏️
                  </button>
                  {isAdmin && income.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleApprove(income.id)}
                        className="text-green-600 hover:text-green-900 mr-3"
                        title="Подтвердить"
                      >
                        ✓
                      </button>
                      <button
                        onClick={() => handleReject(income.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Отклонить"
                      >
                        ✗
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => handleDelete(income.id)}
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
              {editingIncome ? 'Редактировать доход' : 'Новый доход'}
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
                  <option value="salary">Зарплата</option>
                  <option value="bonus">Премия</option>
                  <option value="investment">Инвестиции</option>
                  <option value="gift">Подарок</option>
                  <option value="other">Другое</option>
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
                  <span className="text-sm text-gray-700">Планируемый доход</span>
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
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
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

export default IncomesPage;
