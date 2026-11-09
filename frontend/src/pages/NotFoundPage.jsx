import { useNavigate } from 'react-router-dom';
import { IconError404, IconHome } from '@tabler/icons-react';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="page" style={{ justifyContent: 'center', alignItems: 'center', gap: 16, padding: 40 }}>
      <div className="ci ci-r" style={{ width: 64, height: 64 }}>
        <IconError404 size={28} />
      </div>
      <div style={{ fontSize: 22, fontWeight: 700 }}>404</div>
      <div style={{ fontSize: 14, color: 'var(--mu)', marginBottom: 16 }}>Сторінку не знайдено</div>
      <button className="btn-p" style={{ width: 'auto', padding: '0 28px' }} onClick={() => navigate('/')}>
        <IconHome size={18} /> На головну
      </button>
    </div>
  );
}
