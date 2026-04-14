import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { debtHistoryService } from '../api/services';
import { Navigate } from 'react-router-dom';

export default function DebtHistoryPage() {
  const [selectedCreditor, setSelectedCreditor] = useState(null);

  const { data: historyData, isLoading } = useQuery({
    queryKey: ['debt-history', selectedCreditor],
    queryFn: () => selectedCreditor 
      ? debtHistoryService.getByCreditor(selectedCreditor)
      : debtHistoryService.getAll(),
  });

  if (isLoading) {
    return <div className="text-center py-8">Загрузка...</div>;
  }

  const creditors = historyData || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">История долгов</h1>
        {selectedCreditor && (
          <button
            onClick={() => setSelectedCreditor(null)}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            ← Назад ко всем кредиторам
          </button>
        )}
      </div>

      {!selectedCreditor ? (
        // Список кредиторов с краткой информацией
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {creditors.map((creditor) => (
            <div
              key={creditor.creditor}
              onClick={() => setSelectedCreditor(creditor.creditor)}
              className="bg-white shadow rounded-lg p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{creditor.creditor}</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Текущий долг:</span>
                  <span className="font-medium text-gray-900">
                    {creditor.current_amount.toLocaleString('ru-RU')} ₽
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Минимум:</span>
                  <span className="font-medium text-green-600">
                    {creditor.min_amount.toLocaleString('ru-RU')} ₽
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Максимум:</span>
                  <span className="font-medium text-red-600">
                    {creditor.max_amount.toLocaleString('ru-RU')} ₽
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Записей:</span>
                  <span className="font-medium text-gray-900">{creditor.history.length}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        // Детальная история по выбранному кредитору
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">
              История по кредитору: {selectedCreditor}
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Дата</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Сумма долга</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {creditors[0]?.history.map((record) => (
                  <tr key={record.id}>
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {new Date(record.record_date).toLocaleDateString('ru-RU')}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900 text-right">
                      {record.amount.toLocaleString('ru-RU')} ₽
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}
