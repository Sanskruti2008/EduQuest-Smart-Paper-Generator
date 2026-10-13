import { useEffect, useState } from 'react';
import { LoaderCircle, LogOut, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  AssignedTasksSection,
  FloatingChatButton,
  MyPapersSection,
  ModerationSection,
  OverviewSection,
  PaperGenerationSection,
  QuestionBankSection,
  Sidebar,
  TopNav,
} from '../components/faculty-dashboard';
import type {
  FacultyProfile,
  FacultyResponsibilities,
} from '../components/faculty-dashboard/types';
import { API_CONFIG } from '../utils/constants';
import { getSupabaseClient } from '../lib/supabase';

type FacultyProfileResponse = {
  success: boolean;
  faculty: FacultyProfile;
  responsibilities: FacultyResponsibilities;
  message?: string;
  error?: string;
};

export default function FacultyDashboard() {
  const navigate = useNavigate();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [activeSection, setActiveSection] = useState('dashboard');
  const [profile, setProfile] = useState<FacultyProfile | null>(null);
  const [responsibilities, setResponsibilities] = useState<FacultyResponsibilities | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileRetry, setProfileRetry] = useState(0);

  useEffect(() => {
    if (!sessionStorage.getItem('facultyAuthenticated')) {
      navigate('/', { replace: true });
      return;
    }
    const initialSection = sessionStorage.getItem('facultyInitialSection');
    if (initialSection) {
      setActiveSection(initialSection);
      sessionStorage.removeItem('facultyInitialSection');
    }
  }, [navigate]);

  useEffect(() => {
    const controller = new AbortController();
    let unsubscribeAuthListener = () => {};

    const loadProfile = async () => {
      if (!sessionStorage.getItem('facultyAuthenticated')) return;
      let token: string | null;
      try {
        const supabase = getSupabaseClient();
        const { data: authListener } = supabase.auth.onAuthStateChange(
          (_event, session) => {
            if (session?.access_token) {
              sessionStorage.setItem('authToken', session.access_token);
            } else {
              sessionStorage.removeItem('authToken');
            }
          }
        );
        unsubscribeAuthListener = () => authListener.subscription.unsubscribe();
        const { data, error } = await supabase.auth.getSession();
        if (error) throw error;
        token = data.session?.access_token ?? null;
      } catch (error) {
        if (!controller.signal.aborted) {
          setProfileError(
            error instanceof Error
              ? error.message
              : 'Unable to restore your Supabase session.'
          );
        }
        return;
      }
      if (!token) {
        sessionStorage.removeItem('facultyAuthenticated');
        setProfileError('Your faculty session is missing. Please sign in again.');
        return;
      }
      sessionStorage.setItem('authToken', token);
      setProfileError(null);
      try {
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/faculty/me`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        const data = await response.json().catch(() => null) as FacultyProfileResponse | null;
        if (import.meta.env.DEV) {
          console.info('/api/faculty/me dashboard response:', {
            status: response.status,
            success: Boolean(data?.success),
            message: data?.message ?? null,
            facultyProfileReturned: Boolean(data?.faculty),
          });
        }
        if (
          !response.ok
          || !data?.success
          || !data.faculty
          || !data.responsibilities
          || data.faculty.role !== 'faculty'
          || !data.faculty.is_active
        ) {
          const message = response.status === 401
            ? 'Your session has expired. Please log in again.'
            : response.status === 404
              ? 'Your faculty account is not linked correctly. Contact the administrator.'
              : response.status === 500
                ? 'Unable to load faculty profile. Please try again.'
                : data?.message || data?.error || `Faculty profile request failed (HTTP ${response.status}).`;
          throw new Error(message);
        }
        setProfile(data.faculty);
        setResponsibilities(data.responsibilities);
      } catch (error) {
        if (!controller.signal.aborted) {
          const message = error instanceof Error
            ? error.message
            : 'Unable to load faculty profile. Please try again.';
          if (import.meta.env.DEV) {
            console.error('Faculty profile request failed:', message);
          }
          setProfileError(message);
        }
      }
    };

    void loadProfile();
    return () => {
      controller.abort();
      unsubscribeAuthListener();
    };
  }, [profileRetry]);

  useEffect(() => {
    if (!responsibilities) return;
    if (
      (activeSection === 'moderation' && !responsibilities.can_moderate)
      || (
        ['assigned-tasks', 'paper-generation'].includes(activeSection)
        && !responsibilities.can_generate
      )
    ) {
      setActiveSection('dashboard');
    }
  }, [activeSection, responsibilities]);

  const handleLogout = () => {
    try {
      void getSupabaseClient().auth.signOut().then(({ error }) => {
        if (error && import.meta.env.DEV) {
          console.error('Unable to clear Supabase session:', error.message);
        }
      });
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error(
          'Unable to initialize Supabase while signing out:',
          error instanceof Error ? error.message : 'Unknown error'
        );
      }
    }
    sessionStorage.removeItem('facultyAuthenticated');
    sessionStorage.removeItem('facultyName');
    sessionStorage.removeItem('facultyInitialSection');
    sessionStorage.removeItem('authToken');
    navigate('/', { replace: true });
  };

  const sidebarWidth = sidebarCollapsed ? 'w-20' : 'w-72';

  const handleSectionSelect = (section: string) => {
    if (section === 'logout') {
      handleLogout();
      return;
    }
    if (section === 'paper-generation' || section === 'assigned-tasks') {
      if (!responsibilities?.can_generate) return;
    }
    if (section === 'moderation' && !responsibilities?.can_moderate) return;
    if (section === 'question-bank') {
      navigate('/question-bank');
      return;
    }
    setActiveSection(section);
  };

  if (profileError) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--bg)] px-4 text-[var(--text)]">
        <section className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center shadow-xl">
          <h1 className="text-xl font-semibold">Unable to load faculty profile.</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {profileError}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => setProfileRetry(retry => retry + 1)}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 px-4 py-2 text-sm font-semibold text-white"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 rounded-xl border border-[var(--border)] px-4 py-2 text-sm font-semibold"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </div>
        </section>
      </main>
    );
  }

  if (!profile || !responsibilities) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--bg)] text-[var(--text)]">
        <div className="flex items-center gap-3 rounded-2xl bg-[var(--surface)] px-6 py-4 text-sm shadow-lg">
          <LoaderCircle className="h-5 w-5 animate-spin text-amber-600" />
          Loading faculty profile...
        </div>
      </main>
    );
  }

  const responsibilityLabel = responsibilities.can_generate && responsibilities.can_moderate
    ? 'Paper Setter • Moderator'
    : responsibilities.can_generate
      ? 'Paper Setter'
      : responsibilities.can_moderate
        ? 'Moderator'
        : profile.role.charAt(0).toUpperCase() + profile.role.slice(1);
  const facultyName = profile.name?.trim() || profile.email?.trim() || 'Name not provided';

  const renderSection = () => {
    switch (activeSection) {
      case 'dashboard':
        return (
          <OverviewSection
            facultyName={facultyName}
            responsibilities={responsibilities}
            onSectionSelect={handleSectionSelect}
          />
        );
      case 'assigned-tasks':
        return responsibilities.can_generate
          ? <AssignedTasksSection onSectionSelect={handleSectionSelect} />
          : null;
      case 'question-bank':
        return <QuestionBankSection viewMode={viewMode} onViewModeChange={setViewMode} />;
      case 'paper-generation':
        return responsibilities.can_generate ? <PaperGenerationSection /> : null;
      case 'my-papers':
        return <MyPapersSection />;
      case 'moderation':
        return responsibilities.can_moderate ? <ModerationSection /> : null;
      default:
        return (
          <OverviewSection
            facultyName={facultyName}
            responsibilities={responsibilities}
            onSectionSelect={handleSectionSelect}
          />
        );
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
          canGenerate={responsibilities.can_generate}
          canModerate={responsibilities.can_moderate}
        />

        <main className="flex-1">
          <TopNav
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            department={profile.department}
            facultyName={facultyName}
            responsibilityLabel={responsibilityLabel}
          />

          {renderSection()}
        </main>
      </div>

      <FloatingChatButton />
    </div>
  );
}
