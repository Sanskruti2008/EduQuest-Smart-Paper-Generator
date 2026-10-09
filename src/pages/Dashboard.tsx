import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, GraduationCap, LoaderCircle, ShieldCheck, X } from 'lucide-react';
import { Hero } from '../components/ui/hero';
import { API_CONFIG } from '../utils/constants';
import ThemeToggle from '../components/ThemeToggle';

const Dashboard = () => {
  const navigate = useNavigate();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [credentials, setCredentials] = useState({ email: '', password: '', role: 'faculty' });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Admin and faculty both obtain signed backend tokens before entering
    // protected dashboards.
    const roles: Record<string, { email: string, pass?: string, path: string, authKey: string }> = {
      admin: { email: 'admin@eduquest.ai', path: '/admin-dashboard', authKey: 'adminAuthenticated' },
      faculty: { email: 'faculty@eduquest.ai', path: '/faculty-dashboard', authKey: 'facultyAuthenticated' }
    };

    const targetRole = roles[credentials.role];

    if (!targetRole || credentials.email === '' || credentials.password === '') {
      setError(`Please enter an email and password for ${credentials.role}`);
      return;
    }

    setIsSubmitting(true);
    try {
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/${credentials.role === 'admin' ? 'admin' : 'faculty'}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: credentials.email,
            password: credentials.password
          })
        });
        const data = await response.json();

        if (!response.ok) {
          setError(data.error || `Invalid ${credentials.role} credentials`);
          return;
        }

        sessionStorage.setItem(targetRole.authKey, 'true');
        sessionStorage.setItem('authToken', data.token);
        if (credentials.role === 'admin') {
          sessionStorage.setItem('adminToken', data.token);
        }
        setShowLoginModal(false);
        navigate(targetRole.path);
        return;
    } catch {
      setError('Unable to reach authentication service. Please try again.');
      return;
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="landing-page min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <div className="fixed right-4 top-4 z-30">
        <ThemeToggle />
      </div>
      {/* Hero Section with Animated Canvas */}
      <Hero />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
        {/* Title Section */}
        <div id="dashboard-selection" className="text-center mb-12 md:mb-16 scroll-mt-24">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 text-[var(--text)]">
            Choose Your Dashboard
          </h1>
          <p className="text-xl text-[var(--text-muted)] max-w-2xl mx-auto">
            Select the appropriate dashboard based on your role to access personalized features and tools
          </p>
        </div>

        {/* Dashboard Selection Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12 max-w-5xl mx-auto mb-16">
          <button
            onClick={() => setShowLoginModal(true)}
            className="text-left no-underline rounded-[20px] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/30"
          >
            <div className="bg-[var(--surface)] rounded-[20px] p-6 md:p-10 border border-[var(--border)] shadow-[var(--shadow)] hover:-translate-y-1 hover:shadow-[0_14px_36px_rgba(0,0,0,0.10)] transition-all duration-200 cursor-pointer group h-full">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 rounded-xl bg-[var(--accent-soft)] flex items-center justify-center group-hover:scale-105 transition-transform">
                  <GraduationCap className="w-6 h-6 text-[var(--accent-text)]" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-[var(--text)] group-hover:text-[var(--accent-text)] transition-colors">
                    Faculty
                  </h3>
                  <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--accent-text)] bg-[var(--accent-soft)] px-3 py-1 rounded-full mt-2">
                    <Check className="w-3.5 h-3.5" aria-hidden="true" />
                    Full Access
                  </span>
                </div>
              </div>
              <p className="text-[var(--text-muted)] text-base leading-relaxed mb-6">
                Create professional question papers with AI assistance, moderate assigned papers, manage question banks, organize assessments, and export in multiple formats.
              </p>
              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-2 text-sm text-[var(--text)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-text)]"></div>
                  <span>AI-Powered Paper Generation</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[var(--text)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-text)]"></div>
                  <span>Question Bank Management</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[var(--text)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-text)]"></div>
                  <span>Export to PDF/DOCX</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[var(--text)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-text)]"></div>
                  <span>Moderation & Final Review</span>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="bg-[var(--accent-soft)] text-[var(--accent-text)] px-3 py-1.5 rounded-full font-medium hover:brightness-95 transition-colors">Create</span>
                <span className="bg-[var(--accent-soft)] text-[var(--accent-text)] px-3 py-1.5 rounded-full font-medium hover:brightness-95 transition-colors">Manage</span>
                <span className="bg-[var(--accent-soft)] text-[var(--accent-text)] px-3 py-1.5 rounded-full font-medium hover:brightness-95 transition-colors">Export</span>
                <span className="bg-[var(--accent-soft)] text-[var(--accent-text)] px-3 py-1.5 rounded-full font-medium hover:brightness-95 transition-colors">Moderate</span>
              </div>
            </div>
          </button>

          <button
            onClick={() => { setCredentials({ ...credentials, role: 'admin' }); setShowLoginModal(true); }}
            className="text-left no-underline rounded-[20px] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/30"
          >
            <div className="bg-[var(--surface)] rounded-[20px] p-6 md:p-10 border border-[var(--border)] shadow-[var(--shadow)] hover:-translate-y-1 hover:shadow-[0_14px_36px_rgba(0,0,0,0.10)] transition-all duration-200 cursor-pointer group h-full">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 rounded-xl bg-[var(--accent-soft)] flex items-center justify-center group-hover:scale-105 transition-transform">
                  <ShieldCheck className="w-6 h-6 text-[var(--accent-text)]" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-[var(--text)] group-hover:text-[var(--accent-text)] transition-colors">
                    Administrator
                  </h3>
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent-text)] mt-1">
                    System Control
                  </span>
                </div>
              </div>
              <p className="text-[var(--text-muted)] text-base leading-relaxed mb-6">
                Manage users, assign roles, configure subjects, and store finalized papers by course and semester.
              </p>
            </div>
          </button>

        </div>

        {/* Info Section */}
        <div className="bg-[var(--surface-2)] rounded-[20px] p-8 md:p-10 border border-[var(--border)] shadow-[var(--shadow)]">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl md:text-3xl font-bold text-[var(--text)] mb-4">
              AI-Powered Question Paper Generation
            </h2>
            <p className="text-[var(--text-muted)] text-lg mb-6">
              EduQuest.ai combines advanced AI technology with intuitive design to help educators create 
              professional question papers in minutes and students practice effectively.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
              <div>
                <h4 className="font-bold text-[var(--text)] mb-2">For Faculty</h4>
                <p className="text-sm text-[var(--text-muted)]">Generate papers, manage questions, export to PDF/DOCX</p>
              </div>
              <div>
                <h4 className="font-bold text-[var(--text)] mb-2">For Students</h4>
                <p className="text-sm text-[var(--text-muted)]">Practice questions, track progress, prepare for exams</p>
              </div>
              <div>
                <h4 className="font-bold text-[var(--text)] mb-2">AI-Assisted</h4>
                <p className="text-sm text-[var(--text-muted)]">Smart difficulty balancing and content suggestions</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="login-modal-title"
            className="bg-[var(--surface)] text-[var(--text)] rounded-[24px] max-w-md max-h-[calc(100vh-2rem)] w-full overflow-y-auto p-6 sm:p-8 relative animate-fadeIn shadow-[var(--shadow)] border border-[var(--border)]"
          >
            <div className="absolute top-4 right-14">
              <ThemeToggle />
            </div>
            <button
              onClick={() => {
                setShowLoginModal(false);
                setError('');
                setCredentials({ email: '', password: '', role: 'faculty' });
              }}
              aria-label="Close login"
              className="absolute top-4 right-4 p-2 hover:bg-[var(--accent-soft)] rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/30"
            >
              <X className="w-5 h-5 text-[var(--text-muted)]" />
            </button>

            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--accent-from)] to-[var(--accent-to)] flex items-center justify-center shadow-md">
                <GraduationCap className="w-7 h-7 text-white" />
              </div>
              <div>
                <p className="text-xs font-semibold tracking-wide text-[var(--accent-text)]">EduQuest Core</p>
                <h2 id="login-modal-title" className="text-lg sm:text-2xl font-bold text-[var(--text)]">{credentials.role === 'admin' ? 'Administrator' : 'Faculty'} Sign in</h2>
                <p className="text-sm text-[var(--text-muted)]">Securely sign in to your EduQuest account</p>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <div className="mb-4 grid grid-cols-2 gap-1 rounded-[14px] bg-[var(--bg)] p-1" role="group" aria-label="Choose account type">
              <button
                type="button"
                aria-pressed={credentials.role === 'faculty'}
                onClick={() => setCredentials({ ...credentials, role: 'faculty' })}
                className={`py-2.5 text-sm rounded-[10px] font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/40 ${credentials.role === 'faculty' ? 'bg-gradient-to-r from-[var(--accent-from)] to-[var(--accent-to)] text-white shadow-sm' : 'bg-transparent text-[var(--text-muted)] hover:bg-[var(--surface)]'}`}
              >
                Faculty
              </button>
              <button
                type="button"
                aria-pressed={credentials.role === 'admin'}
                onClick={() => setCredentials({ ...credentials, role: 'admin' })}
                className={`py-2.5 text-sm rounded-[10px] font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/40 ${credentials.role === 'admin' ? 'bg-gradient-to-r from-[var(--accent-from)] to-[var(--accent-to)] text-white shadow-sm' : 'bg-transparent text-[var(--text-muted)] hover:bg-[var(--surface)]'}`}
              >
                Administrator
              </button>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label htmlFor="login-email" className="block text-sm font-semibold text-[var(--text)] mb-2">Email address</label>
                <div className="relative">
                  <input
                    id="login-email"
                    type="email"
                    value={credentials.email}
                    onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
                    placeholder="you@eduquest.ai"
                    required
                    className="w-full h-12 pl-4 pr-3 border border-[var(--input-border)] rounded-xl focus:outline-none focus:ring-[3px] focus:ring-orange-500/20 focus:border-orange-500 bg-[var(--input-bg)] text-[var(--text)] transition duration-200"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="login-password" className="block text-sm font-semibold text-[var(--text)] mb-2">Password</label>
                <input
                  id="login-password"
                  type="password"
                  value={credentials.password}
                  onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                  placeholder="Enter your password"
                  required
                  className="w-full h-12 px-4 border border-[var(--input-border)] rounded-xl focus:outline-none focus:ring-[3px] focus:ring-orange-500/20 focus:border-orange-500 bg-[var(--input-bg)] text-[var(--text)] transition duration-200"
                />
              </div>

              <div className="flex items-center justify-between text-sm text-[var(--text-muted)]">
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 accent-orange-500 rounded focus-visible:ring-2 focus-visible:ring-orange-500/30" />
                  Remember me
                </label>
                <button type="button" className="text-[var(--accent-text)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/30 rounded">Forgot password?</button>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full min-h-12 px-4 py-3 bg-gradient-to-br from-[var(--accent-from)] to-[var(--accent-to)] text-white font-semibold rounded-xl hover:shadow-lg hover:-translate-y-px focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/30 transition-all duration-200 shadow-md disabled:opacity-70 disabled:cursor-wait disabled:hover:translate-y-0"
              >
                {isSubmitting && <LoaderCircle className="mr-2 inline-block h-4 w-4 animate-spin" aria-hidden="true" />}
                {isSubmitting ? 'Signing in...' : `Sign in to ${credentials.role === 'admin' ? 'Administrator' : 'Faculty'} Dashboard`}
              </button>
            </form>

            <div className="mt-5 border-t border-[var(--input-border)] pt-4 text-center">
                <p className="text-xs text-[var(--text-muted)]">Demo guidance</p>
                <p className="text-xs text-[var(--text)]">Email: <span className="font-semibold text-[var(--accent-text)]">{credentials.role}@eduquest.ai</span> — contact your administrator to obtain a secure password.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
