import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ObjectsPage from './pages/ObjectsPage';
import StepPage from './pages/StepPage';
import HistoryPage from './pages/HistoryPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/objects" element={<ObjectsPage />} />
        <Route path="/objects/:objectId/steps/:stepNumber" element={<StepPage />} />
        <Route path="/objects/:objectId/history" element={<HistoryPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
