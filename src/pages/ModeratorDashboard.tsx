import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ModeratorDashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('facultyAuthenticated') || sessionStorage.getItem('moderatorAuthenticated');
    if (!isAuthenticated) {
      navigate('/', { replace: true });
      return;
    }
    sessionStorage.setItem('facultyInitialSection', 'moderation');
    navigate('/faculty-dashboard', { replace: true });
  }, [navigate]);

  return null;
}
