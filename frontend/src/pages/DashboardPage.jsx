import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { debtService, analyticsService, debtHistoryService } from '../api/services';

export default function DashboardPage() {
  const [period, setPeriod] = useState('month');

  const { data: debts, isLoading: debtsLoading } = useQuery({
    queryKey: ['debts'],
    queryFn: () => debtService.getAll(),
  });

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['analytics', 'debt', period],
    queryFn: () => analyticsService.getDebtAnalytics({ period }),
  });

  const { data: debtHistory, isLoading: debtHistoryLoading } = useQuery({
    queryKey: ['debt-history'],
    queryFn: () => debtHistoryService.getAll(),
  });

  const totalDebt = useMemo(
    () => debtHistory?.reduce((sum, item) => sum + (item.current_amount || 0), 0) || 0,
    [debtHistory]
  );

  const pendingCount = debts?.filter(d => d.moderation_status === 'pending').length || 0;

  const creditorsCount = debtHistory?.length || 0;

  const byCreditor = useMemo(() => {
    if (!debtHistory || debtHistory.length === 0 || totalDebt <= 0) return [];

    return debtHistory
      .map((item) => ({
        creditor: item.creditor,
        amount: item.current_amount || 0,
        percentage: totalDebt > 0 ? ((item.current_amount || 0) / totalDebt) * 100 : 0,
      }))
      .sort((a, b) => b.amount - a.amount);
  }, [debtHistory, totalDebt]);

  const recentDebtRows = useMemo(() => {
    if (!debtHistory || debtHistory.length === 0) return [];

    return debtHistory
      .flatMap((item) =>
        (item.history || []).map((h) => ({
          id: h.id,
          date: h.record_date,
          creditor: item.creditor,
          amount: h.amount || 0,
        }))
      )
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 5);
  }, [debtHistory]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Дашборд</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Общий долг</dt>
            <dd className="mt-1 text-3xl font-semibold text-red-600">
              {totalDebt.toLocaleString('ru-RU')} ₽
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">На модерации</dt>
            <dd className="mt-1 text-3xl font-semibold text-yellow-600">
              {pendingCount}
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Кредиторов</dt>
            <dd className="mt-1 text-3xl font-semibold text-indigo-600">
              {creditorsCount}
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">Записей</dt>
            <dd className="mt-1 text-3xl font-semibold text-green-600">
              {debts?.length || 0}
            </dd>
          </div>
        </div>
      </div>

      {/* Analytics Section */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">Аналитика долга</h2>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="week">Неделя</option>
              <option value="month">Месяц</option>
              <option value="year">Год</option>
            </select>
          </div>

          {analyticsLoading || debtHistoryLoading ? (
            <div className="text-center py-8">Загрузка...</div>
          ) : analytics ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 rounded-md">
                  <p className="text-sm text-gray-600">Начальный долг</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {analytics.opening_debt?.toLocaleString('ru-RU') || 0} ₽
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-md">
                  <p className="text-sm text-gray-600">Конечный долг</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {totalDebt.toLocaleString('ru-RU')} ₽
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-md">
                  <p className="text-sm text-gray-600">Изменение</p>
                  <p className={`text-xl font-semibold ${
                    (analytics.debt_change || 0) >= 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {(analytics.debt_change || 0) >= 0 ? '+' : ''}
                    {analytics.debt_change?.toLocaleString('ru-RU') || 0} ₽
                  </p>
                </div>
              </div>

              {byCreditor.length > 0 && (
                <div>
                  <h3 className="text-md font-medium text-gray-900 mb-2">По кредиторам</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Кредитор
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Сумма
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            % от общего
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {byCreditor.map((item, idx) => (
                          <tr key={idx}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {item.creditor}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                              {item.amount?.toLocaleString('ru-RU')} ₽
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                              {item.percentage?.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">Нет данных для отображения</div>
          )}
        </div>
      </div>

      {/* Recent Debts */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Последние записи долгов</h2>
          {debtHistoryLoading ? (
            <div className="text-center py-8">Загрузка...</div>
          ) : recentDebtRows.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Дата
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Кредитор
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Сумма
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      Статус
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentDebtRows.map((debt) => (
                    <tr key={debt.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(debt.date).toLocaleDateString('ru-RU')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {debt.creditor}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                        {debt.amount?.toLocaleString('ru-RU')} ₽
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                          Импортировано
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">Нет записей</div>
          )}
        </div>
      </div>
    </div>
  );
}
