import { useNavigate } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="page not-found">
      <h1>404</h1>
      <p>Page not found</p>
      <button className="submit-btn" onClick={() => navigate('/')}>
        Go home
      </button>
    </div>
  );
}
