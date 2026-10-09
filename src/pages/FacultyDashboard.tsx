import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import {
  AssignedTasksSection,
  FloatingChatButton,
  MyPapersSection,
  ModerationSection,
  OverviewSection,
  PaperGenerationSection,
  QuestionBankSection,
  Sidebar,
  TopNav
} from '../components/faculty-dashboard';

export default function FacultyDashboard() {
  const navigate = useNavigate();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [activeSection, setActiveSection] = useState('dashboard');

  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('facultyAuthenticated');
    if (!isAuthenticated) {
      navigate('/', { replace: true });
    }
    const initialSection = sessionStorage.getItem('facultyInitialSection');
    if (initialSection) {
      setActiveSection(initialSection);
      sessionStorage.removeItem('facultyInitialSection');
    }
  }, [navigate]);

  const sidebarWidth = sidebarCollapsed ? 'w-20' : 'w-72';

  const handleSectionSelect = (section: string) => {
    if (section === 'logout') {
      sessionStorage.removeItem('facultyAuthenticated');
      navigate('/', { replace: true });
      return;
    }
    if (section === 'question-bank') {
      navigate('/question-bank');
      return;
    }
    setActiveSection(section);
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'dashboard':
        return <OverviewSection onSectionSelect={handleSectionSelect} />;
      case 'assigned-tasks':
        return <AssignedTasksSection onSectionSelect={handleSectionSelect} />;
      case 'question-bank':
        return <QuestionBankSection viewMode={viewMode} onViewModeChange={setViewMode} />;
      case 'paper-generation':
        return <PaperGenerationSection />;
      case 'my-papers':
        return <MyPapersSection />;
      case 'moderation':
        return <ModerationSection />;
      default:
        return <OverviewSection />;
    }
  };

  return (
    <div className="faculty-dashboard min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <div className="flex">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          widthClass={sidebarWidth}
          activeKey={activeSection}
          onSelect={handleSectionSelect}
        />

        <main className="flex-1">
          <TopNav
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            darkMode={theme === 'dark'}
            onToggleDarkMode={toggleTheme}
          />

          {renderSection()}
        </main>
      </div>

      <FloatingChatButton />
    </div>
  );
}
