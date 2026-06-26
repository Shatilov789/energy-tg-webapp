import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ObjectsPage from './pages/ObjectsPage';
import StepPage from './pages/StepPage';
import HistoryPage from './pages/HistoryPage';
import NotificationsPage from './pages/NotificationsPage';
import AdminPage from './pages/AdminPage';
import ObjectLogPage from './pages/ObjectLogPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/objects" element={<ObjectsPage />} />
        <Route path="/objects/:objectId/steps/:stepNumber" element={<StepPage />} />
        <Route path="/objects/:objectId/history" element={<HistoryPage />} />
        <Route path="/objects/:objectId/log" element={<ObjectLogPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
