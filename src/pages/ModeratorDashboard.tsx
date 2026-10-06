import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ModeratorDashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('teacherAuthenticated') || sessionStorage.getItem('moderatorAuthenticated');
    if (!isAuthenticated) {
      navigate('/', { replace: true });
      return;
    }
    sessionStorage.setItem('teacherInitialSection', 'moderation');
    navigate('/teacher-dashboard', { replace: true });
  }, [navigate]);

  return null;
}
