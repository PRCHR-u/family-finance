import { createBrowserRouter, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import DebtsPage from './pages/DebtsPage';
import ExpensesPage from './pages/ExpensesPage';
import IncomesPage from './pages/IncomesPage';

// Placeholder pages - will be implemented next
const CreditCardsPage = () => <div className="p-6"><h1 className="text-2xl font-bold">Кредитные карты</h1><p className="mt-4 text-gray-600">Страница в разработке...</p></div>;
const PendingPage = () => <div className="p-6"><h1 className="text-2xl font-bold">На модерации</h1><p className="mt-4 text-gray-600">Страница в разработке...</p></div>;
const UsersPage = () => <div className="p-6"><h1 className="text-2xl font-bold">Пользователи</h1><p className="mt-4 text-gray-600">Страница в разработке...</p></div>;
const AuditLogsPage = () => <div className="p-6"><h1 className="text-2xl font-bold">Аудит логи</h1><p className="mt-4 text-gray-600">Страница в разработке...</p></div>;

function PrivateRoute({ children, adminOnly = false }) {
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  let user = null;
  
  try {
    if (userStr && userStr !== 'undefined' && userStr !== 'null') {
      user = JSON.parse(userStr);
    }
  } catch (e) {
    console.error('Failed to parse user from localStorage:', e);
    user = null;
  }
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  if (adminOnly && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/',
    element: (
      <PrivateRoute>
        <Layout />
      </PrivateRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'debts',
        element: <DebtsPage />,
      },
      {
        path: 'expenses',
        element: <ExpensesPage />,
      },
      {
        path: 'incomes',
        element: <IncomesPage />,
      },
      {
        path: 'credit-cards',
        element: <CreditCardsPage />,
      },
      {
        path: 'pending',
        element: (
          <PrivateRoute adminOnly>
            <PendingPage />
          </PrivateRoute>
        ),
      },
      {
        path: 'users',
        element: (
          <PrivateRoute adminOnly>
            <UsersPage />
          </PrivateRoute>
        ),
      },
      {
        path: 'audit-logs',
        element: (
          <PrivateRoute adminOnly>
            <AuditLogsPage />
          </PrivateRoute>
        ),
      },
    ],
  },
]);
