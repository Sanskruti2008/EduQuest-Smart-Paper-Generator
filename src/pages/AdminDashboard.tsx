import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_CONFIG } from '../utils/constants';
import {
  Bell,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  FileCheck,
  FileUp,
  FileText,
  LayoutDashboard,
  LogOut,
  Printer,
  Search,
  Settings,
  ShieldCheck,
  UserCog,
  Users,
  Wand2,
  LineChart
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';
import { motion } from 'framer-motion';
import QuestionPaperUpload from '../components/QuestionPaperUpload';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

type AdminDashboardStats = {
  total_papers: number;
  total_questions: number;
  papers_by_branch: Record<string, number>;
  papers_by_semester: Array<{ branch: string; semester: string; count: number }>;
};

type AdminStatsResponse = {
  success: boolean;
  stats: AdminDashboardStats;
};

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');

  const sidebarItems = [
    { key: 'overview', label: 'Dashboard Overview', icon: LayoutDashboard },
    { key: 'upload', label: 'Upload Question Paper', icon: FileUp },
    { key: 'rua', label: 'RUA Extraction', icon: FileText },
    { key: 'faculty', label: 'Faculty Management', icon: Users },
    { key: 'assignment', label: 'Assign Duties', icon: UserCog },
    { key: 'finalized', label: 'Finalized Papers', icon: FileCheck },
    { key: 'review', label: 'Review Papers', icon: FileCheck },
    { key: 'workflow', label: 'Approval Workflow', icon: ClipboardCheck },
    { key: 'logout', label: 'Logout', icon: LogOut }
  ];

  const handleSectionSelect = (key: string) => {
    if (key === 'logout') {
      sessionStorage.removeItem('adminAuthenticated');
      sessionStorage.removeItem('adminToken');
      sessionStorage.removeItem('authToken');
      navigate('/', { replace: true });
      return;
    }
    setActiveSection(key);
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'overview':
        return <AdminOverview />;
      case 'upload':
        return <QuestionPaperUpload />;
      case 'rua':
        return <AdminRuaExtraction />;
      case 'faculty':
        return <FacultyManagement />;
      case 'assignment':
        return <PaperAssignment />;
      case 'finalized':
        return <FinalizedPapers />;
      case 'review':
        return (
          <section className="px-4 py-8 md:px-8">
            <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6 flex flex-col items-center justify-center min-h-[400px]">
              <ShieldCheck className="h-16 w-16 text-amber-300 mb-4" />
              <h2 className="text-xl font-semibold text-slate-700">Section Under Construction</h2>
              <p className="text-slate-500 mt-2">The Review Papers module is being built.</p>
            </div>
          </section>
        );
      case 'workflow':
        return <ApprovalWorkflow />;
      default:
        return (
          <section className="px-4 py-8 md:px-8">
            <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6 flex flex-col items-center justify-center min-h-[400px]">
              <ShieldCheck className="h-16 w-16 text-amber-300 mb-4" />
              <h2 className="text-xl font-semibold text-slate-700">Section Under Construction</h2>
              <p className="text-slate-500 mt-2">The {activeSection} module is being built.</p>
            </div>
          </section>
        );
    }
  };

  return (
    <div className="admin-dashboard flex min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <aside className={`${sidebarCollapsed ? 'w-20' : 'w-72'} hidden lg:flex flex-col border-r border-[var(--border)] bg-[var(--surface)] backdrop-blur-xl shadow-xl transition-all duration-300`}>
        <div className="flex items-center justify-between px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 text-white flex items-center justify-center shadow-lg">
              <ShieldCheck className="h-5 w-5" />
            </div>
            {!sidebarCollapsed && (
              <div>
                <p className="text-lg font-bold text-slate-800">EduQuest</p>
                <p className="text-xs font-semibold text-amber-600 tracking-wide uppercase">SysAdmin</p>
              </div>
            )}
          </div>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="flex items-center justify-center h-8 w-8 rounded-xl bg-[var(--surface-2)] shadow-sm hover:shadow-md transition text-[var(--text-muted)]"
          >
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex-1 px-3 pb-6 overflow-y-auto mt-4">
          <ul className="space-y-2">
            {sidebarItems.map((item) => (
              <li key={item.key}>
                <button
                  onClick={() => handleSectionSelect(item.key)}
                  className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${
                    activeSection === item.key
                      ? 'bg-gradient-to-r from-[var(--accent-from)] to-[var(--accent-to)] text-white shadow-md'
                      : 'text-slate-600 hover:bg-white/80 hover:text-slate-900'
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {!sidebarCollapsed && item.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <main className="flex-1 overflow-y-auto h-screen relative">
        <header className="sticky top-0 z-20 border-b border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur-xl shadow-sm">
          <div className="flex flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="flex lg:hidden items-center justify-center h-10 w-10 rounded-2xl bg-[var(--surface-2)] shadow-sm"
              >
                <LayoutDashboard className="h-5 w-5" />
              </button>
              <div>
                <p className="text-sm font-medium text-amber-600">EduQuest Core</p>
                <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600">System Admin Portal</h1>
              </div>
            </div>

            <div className="flex flex-1 items-center gap-3 md:justify-end">
              <div className="flex-1 md:max-w-xs">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    placeholder="Search faculty, papers..."
                    className="w-full rounded-2xl border border-[var(--input-border)] bg-[var(--input-bg)] py-2 pl-10 pr-4 text-sm text-[var(--text)] shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <button className="flex items-center justify-center h-10 w-10 rounded-2xl bg-white shadow-sm relative">
                <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 animate-pulse"></span>
                <Bell className="h-4 w-4 text-slate-600" />
              </button>

              <ThemeToggle />

              <div className="flex items-center gap-3 rounded-2xl bg-white pl-2 pr-4 py-1.5 shadow-sm border border-white/60">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 border-2 border-white shadow-sm"></div>
                <div className="hidden md:block text-left">
                  <p className="text-xs font-bold text-slate-800 leading-tight">Admin Principal</p>
                  <p className="text-[10px] text-slate-500 leading-tight">Super User</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {renderSection()}
      </main>
    </div>
  );
}

// Sub components

function AdminOverview() {
  const navigate = useNavigate();
  const [dashboardStats, setDashboardStats] = useState<AdminStatsResponse | null>(null);
  const [statsError, setStatsError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = sessionStorage.getItem('adminToken');
        if (!token) {
          throw new Error('Admin authentication is required to load dashboard data.');
        }
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.status === 401 || response.status === 403) {
          sessionStorage.removeItem('adminAuthenticated');
          sessionStorage.removeItem('adminToken');
          sessionStorage.removeItem('authToken');
          navigate('/', { replace: true });
          return;
        }
        const data = await response.json() as AdminStatsResponse;
        if (!response.ok || !data.success) {
          throw new Error('Unable to load dashboard statistics.');
        }
        setDashboardStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
        setStatsError(error instanceof Error ? error.message : 'Unable to load dashboard statistics.');
      }
    };
    fetchStats();
  }, []);

  const stats = dashboardStats ? [
    { label: 'Total Papers Generated', value: dashboardStats.stats.total_papers },
    { label: 'Total Questions', value: dashboardStats.stats.total_questions },
    { label: 'Branches with Papers', value: Object.keys(dashboardStats.stats.papers_by_branch).length },
  ] : [];
  const chartData = dashboardStats?.stats.papers_by_semester.map(({ branch, semester, count }) => ({
    name: `${branch} · Semester ${semester}`,
    papers: count,
  })) ?? [];

  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      {stats.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.map((stat, index) => (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 * index }}
                        className="bg-white/80 backdrop-blur-md rounded-2xl p-5 shadow-sm border border-white/60">
              <p className="text-sm font-medium text-slate-500">{stat.label}</p>
              <h3 className="text-3xl font-bold text-slate-800 mt-2">{stat.value}</h3>
            </motion.div>
          ))}
        </div>
      )}

      {statsError && (
        <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {statsError}
        </p>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
          <h3 className="text-lg font-bold text-slate-800 mb-4">Papers by Branch and Semester</h3>
          <div className="h-64">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorPapers" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 12}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 12}} dx={-10} />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Area type="monotone" dataKey="papers" stroke="#f59e0b" strokeWidth={3} fillOpacity={1} fill="url(#colorPapers)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-slate-500" role="status">
                {statsError ? 'Paper data could not be loaded.' : dashboardStats ? 'No paper records are available yet.' : 'Loading paper data…'}
              </div>
            )}
          </div>
        </div>

        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
          <h3 className="text-lg font-bold text-slate-800 mb-4">Pending Approvals</h3>
          <div className="min-h-64 flex items-center justify-center rounded-xl bg-slate-50 px-6 text-center">
            <p className="text-sm text-slate-500" role="status">
              Pending approval records are not available yet.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function AdminRuaExtraction() {
  const [subjects, setSubjects] = useState<Array<{ subject_id: number; subject_name: string; subject_code?: string }>>([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [branch, setBranch] = useState('');
  const [semester, setSemester] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [totalValues, setTotalValues] = useState({ R: 0, U: 0, A: 0, Total: 0 });
  const [units, setUnits] = useState<Array<{ unit_key: string; unit_name: string; R: number; U: number; A: number; Total: number }>>([]);

  useEffect(() => {
    const loadSubjects = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/syllabus/subjects`);
        const data = await response.json();
        if (response.ok && data?.success) {
          setSubjects(data.subjects || []);
        }
      } catch (error) {
        console.error('Failed to load subjects:', error);
      }
    };
    loadSubjects();
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const resetFlow = () => {
    setFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl('');
    setExtracting(false);
    setSaving(false);
    setStatusMessage('');
    setErrorMessage('');
    setTotalValues({ R: 0, U: 0, A: 0, Total: 0 });
    setUnits([]);
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setErrorMessage('');
    setStatusMessage('');
    setUnits([]);
    setTotalValues({ R: 0, U: 0, A: 0, Total: 0 });

    const token = sessionStorage.getItem('adminToken');
    if (!token) {
      setErrorMessage('Admin login required to extract RUA values.');
      return;
    }

    setExtracting(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (selectedSubject) formData.append('subject_name', selectedSubject);
      if (branch) formData.append('branch', branch);
      if (semester) formData.append('semester', semester);

      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/admin/rua/extract`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await response.json();

      if (!response.ok || !data?.success) {
        throw new Error(data?.error || 'Unable to extract RUA values');
      }

      setUnits((data.units || []).map((unit: any) => ({
        unit_key: unit.unit_key,
        unit_name: unit.unit_name,
        R: Number(unit.R || 0),
        U: Number(unit.U || 0),
        A: Number(unit.A || 0),
        Total: Number(unit.Total || 0),
      })));
      setTotalValues({
        R: Number(data.total?.R || 0),
        U: Number(data.total?.U || 0),
        A: Number(data.total?.A || 0),
        Total: Number(data.total?.Total || 0),
      });
      setStatusMessage('RUA values extracted. Review them below and confirm to save.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to extract RUA values');
    } finally {
      setExtracting(false);
    }
  };

  const updateUnitField = (index: number, field: 'unit_name' | 'R' | 'U' | 'A' | 'Total', value: string) => {
    setUnits((current) => current.map((unit, unitIndex) => {
      if (unitIndex !== index) return unit;
      if (field === 'unit_name') {
        return { ...unit, unit_name: value };
      }
      return { ...unit, [field]: Number(value || 0) } as typeof unit;
    }));
  };

  const handleSave = async () => {
    if (!selectedSubject) {
      setErrorMessage('Select a subject before saving the confirmed RUA values.');
      return;
    }
    if (!units.length) {
      setErrorMessage('Extract RUA values first.');
      return;
    }

    const token = sessionStorage.getItem('adminToken');
    if (!token) {
      setErrorMessage('Admin login required to save RUA values.');
      return;
    }

    setSaving(true);
    setErrorMessage('');
    try {
      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/admin/rua/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          subject_name: selectedSubject,
          branch,
          semester,
          units,
        }),
      });

      const data = await response.json();
      if (!response.ok || !data?.success) {
        throw new Error(data?.error || 'Unable to save RUA values');
      }

      setStatusMessage('Confirmed RUA values were saved to the database.');
      resetFlow();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save RUA values');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="px-4 py-8 md:px-8">
      <div className="rounded-2xl bg-white/80 backdrop-blur-md shadow-sm border border-white/60 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold text-amber-600 uppercase tracking-wide">Admin-only section</p>
            <h2 className="mt-2 text-2xl font-bold text-slate-800">RUA Extraction</h2>
            <p className="mt-3 max-w-2xl text-sm text-slate-600">
              Upload a PDF, let the system extract the RUA values automatically, then confirm the values and save them directly into the database.
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800">Upload PDF</h3>
            <p className="mt-2 text-sm text-slate-500">Choose a RUA PDF and the system will extract values automatically.</p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-600">Subject</label>
                <select
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-400"
                >
                  <option value="">Select subject before saving</option>
                  {subjects.map((subject) => (
                    <option key={subject.subject_id} value={subject.subject_name}>{subject.subject_name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">Branch</label>
                  <input
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    placeholder="Optional"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-400"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-600">Semester</label>
                  <input
                    value={semester}
                    onChange={(e) => setSemester(e.target.value)}
                    placeholder="Optional"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-400"
                  />
                </div>
              </div>

              <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50 px-4 py-8 text-center transition hover:border-amber-500 hover:bg-amber-100/60">
                <FileText className="h-8 w-8 text-amber-600" />
                <span className="mt-3 text-sm font-semibold text-slate-800">Click to upload PDF</span>
                <span className="mt-1 text-xs text-slate-500">The file is extracted as soon as it is chosen.</span>
                <input
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>

              {file && (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                  <p className="font-semibold text-slate-800">{file.name}</p>
                  <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              )}

              <button
                onClick={handleSave}
                disabled={!units.length || !selectedSubject || saving}
                className="w-full rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 px-4 py-3 text-sm font-semibold text-white shadow-md transition hover:shadow-lg disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {saving ? 'Saving confirmed RUA values...' : 'Confirm & Save to Database'}
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-800">Preview and confirm</h3>
                <p className="mt-1 text-sm text-slate-500">Review the extracted PDF and edit any values before saving.</p>
              </div>
              {extracting && <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">Extracting</span>}
            </div>

            {statusMessage && (
              <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                {statusMessage}
              </div>
            )}
            {errorMessage && (
              <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {errorMessage}
              </div>
            )}

            <div className="mt-4 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <div className="min-h-[420px] overflow-hidden rounded-2xl border border-slate-200 bg-slate-100">
                {previewUrl ? (
                  <iframe title="RUA PDF preview" src={previewUrl} className="h-[420px] w-full" />
                ) : (
                  <div className="flex h-[420px] items-center justify-center px-6 text-center text-sm text-slate-500">
                    Upload a PDF to preview it here.
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'R', value: totalValues.R },
                    { label: 'U', value: totalValues.U },
                    { label: 'A', value: totalValues.A },
                    { label: 'Total', value: totalValues.Total },
                  ].map((item) => (
                    <div key={item.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-xs font-semibold text-slate-500">TOTAL {item.label}</p>
                      <p className="mt-1 text-2xl font-bold text-slate-800">{item.value}</p>
                    </div>
                  ))}
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <h4 className="text-sm font-bold text-slate-800">Extracted units</h4>
                  <div className="mt-3 space-y-3">
                    {units.length === 0 ? (
                      <p className="text-sm text-slate-500">
                        {extracting ? 'Reading the PDF and extracting values...' : 'No extracted values yet.'}
                      </p>
                    ) : (
                      units.map((unit, index) => (
                        <div key={unit.unit_key} className="rounded-2xl border border-slate-200 bg-white p-3">
                          <div className="mb-3 flex items-center justify-between gap-3">
                            <span className="text-xs font-semibold text-amber-600">{unit.unit_key}</span>
                            <input
                              value={unit.unit_name}
                              onChange={(e) => updateUnitField(index, 'unit_name', e.target.value)}
                              className="w-full max-w-[230px] rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-amber-400"
                            />
                          </div>
                          <div className="grid grid-cols-4 gap-2 text-sm">
                            {(['R', 'U', 'A', 'Total'] as const).map((field) => (
                              <label key={field} className="space-y-1">
                                <span className="text-xs font-semibold text-slate-500">{field}</span>
                                <input
                                  type="number"
                                  value={unit[field]}
                                  onChange={(e) => updateUnitField(index, field, e.target.value)}
                                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-amber-400"
                                />
                              </label>
                            ))}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function FacultyManagement() {
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [facultyList, setFacultyList] = useState<any[]>([]);
  const [loadingFaculty, setLoadingFaculty] = useState(true);
  const [facultyError, setFacultyError] = useState<string | null>(null);

  // Modal styling and state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalCourseOverride, setModalCourseOverride] = useState<string>('');
  const [newFaculty, setNewFaculty] = useState({
    name: '',
    course: '',
    role: 'Paper Setter',
    status: 'Active'
  });

  useEffect(() => {
    const fetchFaculty = async () => {
      const token = sessionStorage.getItem('adminToken');
      if (!token) {
        setFacultyError('Admin token missing. Please log in again.');
        setLoadingFaculty(false);
        return;
      }

      try {
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/admin/faculty`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        const data = await response.json();
        if (!response.ok || !data?.success) {
          throw new Error(data?.error || 'Unable to load faculty list');
        }
        setFacultyList(data.faculty || []);
      } catch (error) {
        setFacultyError(error instanceof Error ? error.message : 'Unable to load faculty list');
      } finally {
        setLoadingFaculty(false);
      }
    };

    fetchFaculty();
  }, []);

  const openAddModal = (courseOverride?: string) => {
    setModalCourseOverride(courseOverride || '');
    setNewFaculty({
      name: '',
      course: courseOverride || '',
      role: 'Paper Setter',
      status: 'Active'
    });
    setIsModalOpen(true);
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = sessionStorage.getItem('adminToken');
    if (!token) {
      setFacultyError('Admin token missing. Please log in again.');
      setIsModalOpen(false);
      return;
    }

    try {
      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/admin/faculty`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newFaculty)
      });
      const data = await response.json();
      if (!response.ok || !data?.success) {
        throw new Error(data?.error || 'Unable to add faculty');
      }
      setFacultyList(data.faculty || []);
      setIsModalOpen(false);
    } catch (error) {
      setFacultyError(error instanceof Error ? error.message : 'Unable to add faculty');
      setIsModalOpen(false);
    }
  };

  const courses = Array.from(new Set(facultyList.map((faculty) => faculty.course))).sort();

  const modalJSX = isModalOpen && (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setIsModalOpen(false)}></div>
      <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl p-6 border border-white/60">
        <h3 className="text-xl font-bold text-slate-800 mb-4">Add New Faculty</h3>
        <form onSubmit={handleAddSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Full Name</label>
            <input
              required
              type="text"
              placeholder="e.g., Dr. Sarah Connor"
              value={newFaculty.name}
              onChange={e => setNewFaculty({ ...newFaculty, name: e.target.value })}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 outline-none focus:ring-2 focus:ring-amber-400"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Course / Department</label>
            <input
              required
              type="text"
              placeholder="e.g., Computer Technology"
              value={newFaculty.course}
              disabled={!!modalCourseOverride}
              onChange={e => setNewFaculty({ ...newFaculty, course: e.target.value })}
              className={`w-full rounded-xl border border-slate-200 p-2.5 outline-none focus:ring-2 focus:ring-amber-400 ${modalCourseOverride ? 'bg-slate-100 text-slate-500' : 'bg-slate-50'}`}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Role</label>
            <select
              value={newFaculty.role}
              onChange={e => setNewFaculty({ ...newFaculty, role: e.target.value })}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 outline-none focus:ring-2 focus:ring-amber-400"
            >
              <option value="Paper Setter">Paper Setter</option>
              <option value="Moderator">Moderator</option>
              <option value="Admin">Admin</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Status</label>
            <select
              value={newFaculty.status}
              onChange={e => setNewFaculty({ ...newFaculty, status: e.target.value })}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 outline-none focus:ring-2 focus:ring-amber-400"
            >
              <option value="Active">Active</option>
              <option value="Reviewing">Reviewing</option>
              <option value="Offline">Offline</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-5 py-2.5 rounded-xl font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-gradient-to-r from-amber-500 to-orange-600 text-white px-5 py-2.5 rounded-xl font-semibold shadow-md hover:shadow-lg transition"
            >
              Save Faculty
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  if (selectedCourse) {
    const courseFaculty = facultyList.filter((faculty) => faculty.course === selectedCourse);
    return (
      <section className="px-4 py-8 md:px-8 space-y-6">
        <div className="flex justify-between items-center bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSelectedCourse(null)} 
              className="p-2 bg-slate-100 hover:bg-slate-200 rounded-xl transition text-slate-600"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <div>
              <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide">Course Faculty Details</p>
              <h2 className="text-2xl font-bold text-slate-800">{selectedCourse}</h2>
            </div>
          </div>
          <button
            onClick={() => openAddModal(selectedCourse)}
            className="hidden sm:block bg-gradient-to-r from-amber-500 to-orange-600 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-md hover:shadow-lg transition"
          >
            + Add Faculty to Course
          </button>
        </div>

        {facultyError && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {facultyError}
          </div>
        )}

        <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-slate-500 bg-slate-50/70">
              <tr>
                <th className="px-6 py-4 font-medium">Faculty Name</th>
                <th className="px-6 py-4 font-medium">System Role</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loadingFaculty ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                    Loading faculty...
                  </td>
                </tr>
              ) : courseFaculty.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                    No faculty found for this course.
                  </td>
                </tr>
              ) : (
                courseFaculty.map((faculty, index) => (
                  <tr key={`${selectedCourse}-${index}`} className="hover:bg-slate-50/50 transition">
                    <td className="px-6 py-4 font-semibold text-slate-800 flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-xs">
                        {faculty.name.charAt(faculty.name.startsWith('Dr.') ? 4 : 6) || faculty.name.charAt(0)}
                      </div>
                      {faculty.name}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700">
                        {faculty.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className={`h-2 w-2 rounded-full ${faculty.status === 'Active' ? 'bg-emerald-500' : faculty.status === 'Reviewing' ? 'bg-amber-500' : 'bg-slate-300'}`}></span>
                        <span className="text-slate-600">{faculty.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="text-amber-600 hover:text-orange-700 font-medium text-sm">Edit</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {modalJSX}
      </section>
    );
  }

  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Faculty Management</h2>
          <p className="text-sm text-slate-500">Manage roles, departments, and access levels.</p>
        </div>
        <button
          onClick={() => openAddModal()}
          className="bg-gradient-to-r from-amber-500 to-orange-600 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-md hover:shadow-lg transition"
        >
          + Add Faculty
        </button>
      </div>

      {facultyError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {facultyError}
        </div>
      )}

      {loadingFaculty ? (
        <div className="rounded-2xl bg-white/80 backdrop-blur-md border border-white/60 px-6 py-10 text-center text-slate-500">
          Loading faculty data...
        </div>
      ) : courses.length === 0 ? (
        <div className="rounded-2xl bg-white/80 backdrop-blur-md border border-white/60 px-6 py-10 text-center text-slate-500">
          No courses found yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {courses.map((course) => {
            const courseFaculty = facultyList.filter((faculty) => faculty.course === course);
            return (
              <button
                key={course}
                onClick={() => setSelectedCourse(course)}
                className="bg-white/80 hover:bg-white backdrop-blur-md rounded-2xl p-6 shadow-sm hover:shadow-md transition-all border border-white/60 text-left group flex items-center justify-between"
              >
                <div>
                  <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-1">Course</p>
                  <h3 className="text-lg font-bold text-slate-800 group-hover:text-amber-600 transition-colors">{course}</h3>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-slate-100 rounded-lg text-xs font-semibold text-slate-600">
                    {courseFaculty.length} Faculty
                  </span>
                  <ChevronRight className="h-5 w-5 text-slate-400 group-hover:text-amber-500 transition-colors" />
                </div>
              </button>
            );
          })}
        </div>
      )}

      {modalJSX}
    </section>
  );
}

function PaperAssignment() {
  const [currentStep, setCurrentStep] = useState(1);
  const [assignmentView, setAssignmentView] = useState<'assign' | 'assigned'>('assign');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedSem, setSelectedSem] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedPaperSetter, setSelectedPaperSetter] = useState('');
  const [selectedModerator, setSelectedModerator] = useState('');
  const [showOtherFacultyPicker, setShowOtherFacultyPicker] = useState('');
  const [showDutyAssignedPopup, setShowDutyAssignedPopup] = useState(false);
  const [assignedStep, setAssignedStep] = useState(1);
  const [selectedAssignedDept, setSelectedAssignedDept] = useState('');
  const [selectedAssignedSemester, setSelectedAssignedSemester] = useState('');
  const [assignedRoles, setAssignedRoles] = useState<Array<{
    id: number;
    department: string;
    departmentCode: string;
    semester: string;
    subject: string;
    paperSetter: string;
    moderator: string;
    assignedAt: string;
  }>>([]);
  
  // Mock department data
  const departments = [
    { id: 'ce', name: 'Computer Engineering', code: 'CE' },
    { id: 'cse', name: 'Computer Science Engineering', code: 'CSE' },
    { id: 'ece', name: 'Electronics & Communication', code: 'ECE' },
    { id: 'mech', name: 'Mechanical Engineering', code: 'MECH' },
    { id: 'civil', name: 'Civil Engineering', code: 'CIVIL' },
  ];
  
  // Mock subjects per department
  const subjectsByDept = {
    'ce': [
      { id: 'iom', name: 'Industrial Organization and Management (IOM)' },
    ],
    'cse': [
      { id: 'dbms', name: 'Database Management Systems' },
      { id: 'os', name: 'Operating Systems' },
      { id: 'ai', name: 'Artificial Intelligence' },
      { id: 'dsa', name: 'Data Structures & Algorithms' },
    ],
    'ece': [
      { id: 'signals', name: 'Signals & Systems' },
      { id: 'circuits', name: 'Digital Circuits' },
      { id: 'comm', name: 'Communication Systems' },
    ],
  };
  
  // Mock faculty per department
  const facultyByDept = {
    'cse': [
      'Dr. Sarah Connor',
      'Prof. Alan Turing',
      'Dr. Grace Hopper',
      'Prof. John von Neumann',
    ],
    'ece': [
      'Dr. Nikola Tesla',
      'Prof. Michael Faraday',
      'Dr. Hedy Lamarr',
    ],
  };
  
  const semesters = ['1', '2', '3', '4', '5', '6'];
  
  // Mock faculty workload data (papers assigned + in progress)
  const facultyWorkload = {
    'cse': {
      'Dr. Sarah Connor': { assigned: 5, inProgress: 2, total: 7 },
      'Prof. Alan Turing': { assigned: 3, inProgress: 1, total: 4 },
      'Dr. Grace Hopper': { assigned: 8, inProgress: 3, total: 11 },
      'Prof. John von Neumann': { assigned: 2, inProgress: 0, total: 2 },
    },
    'ece': {
      'Dr. Nikola Tesla': { assigned: 6, inProgress: 2, total: 8 },
      'Prof. Michael Faraday': { assigned: 4, inProgress: 1, total: 5 },
    },
  };
  
  const getWorkloadColor = (total) => {
    if (total >= 10) return 'bg-red-100 text-red-700 border-red-300';
    if (total >= 7) return 'bg-amber-100 text-amber-700 border-amber-300';
    return 'bg-emerald-100 text-emerald-700 border-emerald-300';
  };

  const selectedDeptData = departments.find(d => d.id === selectedDept);
  const selectedFacultyList = facultyWorkload[selectedDept] || {};
  const deptFaculty = facultyByDept[selectedDept] || [];
  const deptSubjects = subjectsByDept[selectedDept] || [];
  const selectedSubjectData = deptSubjects.find(s => s.id === selectedSubject);

  const handleDeptSelect = (deptId) => {
    setSelectedDept(deptId);
    setSelectedSem('');
    setSelectedSubject('');
    setSelectedPaperSetter('');
    setSelectedModerator('');
    setShowOtherFacultyPicker('');
    setCurrentStep(2);
  };

  const handleSemSelect = (sem) => {
    setSelectedSem(sem);
    setCurrentStep(3);
  };

  const handleSubjectSelect = (subId) => {
    setSelectedSubject(subId);
    setCurrentStep(4);
  };

  const handleBackToDept = () => {
    setSelectedDept('');
    setSelectedSem('');
    setSelectedSubject('');
    setSelectedPaperSetter('');
    setSelectedModerator('');
    setShowOtherFacultyPicker('');
    setCurrentStep(1);
  };

  const handleSetterSelect = (faculty) => {
    setSelectedPaperSetter(faculty);
    setShowOtherFacultyPicker('');
  };

  const handleModeratorSelect = (faculty) => {
    setSelectedModerator(faculty);
    setShowOtherFacultyPicker('');
  };

  const handleCompleteAssignment = () => {
    if (!selectedPaperSetter || !selectedModerator) return;

    const assignmentRecord = {
      id: Date.now(),
      department: selectedDeptData?.name || 'Unknown Department',
      departmentCode: selectedDeptData?.code || 'NA',
      semester: selectedSem,
      subject: selectedSubjectData?.name || 'Unknown Subject',
      paperSetter: selectedPaperSetter,
      moderator: selectedModerator,
      assignedAt: new Date().toLocaleString(),
    };

    setAssignedRoles((prev) => [assignmentRecord, ...prev]);

    setShowDutyAssignedPopup(true);
    handleBackToDept();
    setAssignmentView('assigned');
    setAssignedStep(1);
    setSelectedAssignedDept('');
    setSelectedAssignedSemester('');

    window.setTimeout(() => {
      setShowDutyAssignedPopup(false);
    }, 2200);
  };

  const assignmentHierarchy = assignedRoles.reduce((acc, assignment) => {
    const deptKey = `${assignment.department} (${assignment.departmentCode})`;
    const semKey = `Semester ${assignment.semester}`;

    if (!acc[deptKey]) acc[deptKey] = {};
    if (!acc[deptKey][semKey]) acc[deptKey][semKey] = {};
    if (!acc[deptKey][semKey][assignment.subject]) acc[deptKey][semKey][assignment.subject] = [];

    acc[deptKey][semKey][assignment.subject].push({
      id: `${assignment.id}-setter`,
      role: 'Paper Setter',
      faculty: assignment.paperSetter,
      assignedAt: assignment.assignedAt,
    });

    acc[deptKey][semKey][assignment.subject].push({
      id: `${assignment.id}-moderator`,
      role: 'Moderator',
      faculty: assignment.moderator,
      assignedAt: assignment.assignedAt,
    });

    return acc;
  }, {} as Record<string, Record<string, Record<string, Array<{ id: string; role: string; faculty: string; assignedAt: string }>>>>);

  const totalAssignedRoles = assignedRoles.length * 2;
  const assignedDepartments = Object.keys(assignmentHierarchy);
  const assignedSemesters = selectedAssignedDept
    ? Object.keys(assignmentHierarchy[selectedAssignedDept] || {})
    : [];
  const assignedSubjects = selectedAssignedDept && selectedAssignedSemester
    ? assignmentHierarchy[selectedAssignedDept]?.[selectedAssignedSemester] || {}
    : {};

  const openAssignView = () => {
    setAssignmentView('assign');
  };

  const openAssignedView = () => {
    setAssignmentView('assigned');
    setAssignedStep(1);
    setSelectedAssignedDept('');
    setSelectedAssignedSemester('');
  };

  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      {showDutyAssignedPopup && (
        <div className="fixed top-6 right-6 z-50 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 shadow-lg">
          <p className="text-sm font-semibold text-emerald-700">Duty assigned successfully.</p>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Assign Duties</h2>
          {assignmentView === 'assign' ? (
            <p className="text-sm text-slate-500 mt-1">Step {currentStep} of 4: {
              currentStep === 1 ? 'Select Department' : 
              currentStep === 2 ? 'Select Semester' :
              currentStep === 3 ? 'Select Subject' :
              'Assign Moderator & Setter'
            }</p>
          ) : (
            <p className="text-sm text-slate-500 mt-1">Assigned Step {assignedStep} of 3: {
              assignedStep === 1 ? 'Department' :
              assignedStep === 2 ? 'Semester' :
              'Subject Roles'
            }</p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-slate-200 p-1 bg-white/80">
            <button
              onClick={openAssignView}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition ${
                assignmentView === 'assign'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Create Assignment
            </button>
            <button
              onClick={openAssignedView}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition ${
                assignmentView === 'assigned'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Assigned Roles
            </button>
          </div>

          {assignmentView === 'assign' && (
            <div className="flex gap-1">
              {[1, 2, 3, 4].map((step) => (
                <div key={step} className={`h-1 flex-1 rounded-full transition ${
                  step <= currentStep ? 'bg-amber-500' : 'bg-slate-200'
                }`} style={{ width: '12px' }} />
              ))}
            </div>
          )}

          {assignmentView === 'assigned' && assignedRoles.length > 0 && (
            <div className="flex gap-1">
              {[1, 2, 3].map((step) => (
                <div key={step} className={`h-1 flex-1 rounded-full transition ${
                  step <= assignedStep ? 'bg-emerald-500' : 'bg-slate-200'
                }`} style={{ width: '12px' }} />
              ))}
            </div>
          )}
        </div>
      </div>

      {assignmentView === 'assigned' && (
        <motion.div
          key={`assigned-step-page-${assignedStep}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="bg-white/80 backdrop-blur-md rounded-2xl p-8 shadow-sm border border-white/60 space-y-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-slate-800">Assigned Roles</h3>
              <p className="text-slate-600 mt-1">Page flow: Department → Semester → Subject roles.</p>
            </div>
            <span className="px-3 py-1.5 rounded-full bg-slate-100 text-slate-700 text-xs font-bold">
              {totalAssignedRoles} Role Assignments
            </span>
          </div>

          {assignedRoles.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <p className="font-semibold text-slate-700">No roles assigned yet.</p>
              <p className="text-sm text-slate-500 mt-2">Create an assignment from the Create Assignment page to see it here.</p>
            </div>
          ) : (
            <>
              {assignedStep === 1 && (
                <div className="space-y-5">
                  <p className="text-xs font-bold uppercase tracking-wider text-emerald-600">Page 1: Department</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {assignedDepartments.map((dept) => (
                      <button
                        key={dept}
                        onClick={() => {
                          setSelectedAssignedDept(dept);
                          setSelectedAssignedSemester('');
                          setAssignedStep(2);
                        }}
                        className="rounded-xl border border-slate-200 bg-white p-5 text-left hover:border-emerald-400 hover:bg-emerald-50 transition"
                      >
                        <p className="text-base font-bold text-slate-800">{dept}</p>
                        <p className="text-xs text-slate-500 mt-2">Tap to view semesters</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {assignedStep === 2 && (
                <div className="space-y-5">
                  <p className="text-xs font-bold uppercase tracking-wider text-emerald-600">Page 2: Semester</p>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm text-slate-600">Department: <span className="font-semibold text-slate-800">{selectedAssignedDept}</span></p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {assignedSemesters.map((semester) => (
                      <button
                        key={semester}
                        onClick={() => {
                          setSelectedAssignedSemester(semester);
                          setAssignedStep(3);
                        }}
                        className="rounded-xl border border-slate-200 bg-white p-5 text-left hover:border-emerald-400 hover:bg-emerald-50 transition"
                      >
                        <p className="text-base font-bold text-slate-800">{semester}</p>
                        <p className="text-xs text-slate-500 mt-2">Tap to view subjects and roles</p>
                      </button>
                    ))}
                  </div>
                  <div className="pt-2">
                    <button
                      onClick={() => {
                        setAssignedStep(1);
                        setSelectedAssignedDept('');
                      }}
                      className="px-5 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-100 transition"
                    >
                      ← Back to Departments
                    </button>
                  </div>
                </div>
              )}

              {assignedStep === 3 && (
                <div className="space-y-5">
                  <p className="text-xs font-bold uppercase tracking-wider text-emerald-600">Page 3: Subject Roles</p>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-1">
                    <p className="text-sm text-slate-600">Department: <span className="font-semibold text-slate-800">{selectedAssignedDept}</span></p>
                    <p className="text-sm text-slate-600">Semester: <span className="font-semibold text-slate-800">{selectedAssignedSemester}</span></p>
                  </div>

                  <div className="space-y-4">
                    {Object.entries(assignedSubjects).map(([subject, roles]) => (
                      <div key={`${selectedAssignedDept}-${selectedAssignedSemester}-${subject}`} className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
                        <p className="font-semibold text-slate-800">{subject}</p>
                        <div className="grid md:grid-cols-2 gap-2">
                          {roles.map((roleEntry) => (
                            <div key={roleEntry.id} className="rounded-md border border-slate-200 bg-white px-3 py-2 flex items-center justify-between gap-3">
                              <div>
                                <p className="text-xs text-slate-500">{roleEntry.role}</p>
                                <p className="text-sm font-semibold text-slate-800">{roleEntry.faculty}</p>
                              </div>
                              <span className="text-xs text-slate-500 whitespace-nowrap">{roleEntry.assignedAt}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={() => {
                        setAssignedStep(2);
                        setSelectedAssignedSemester('');
                      }}
                      className="px-5 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-100 transition"
                    >
                      ← Back to Semesters
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </motion.div>
      )}

      {assignmentView === 'assign' && (
        <motion.div
          key={`assign-step-page-${currentStep}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
      {/* Step 1: Department Selection */}
      {currentStep === 1 && (
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-8 shadow-sm border border-white/60 space-y-6 min-h-[400px] flex flex-col justify-center">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-amber-600 mb-2">Page 1: Department</p>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">Choose Department</h3>
            <p className="text-slate-600 mb-8">Select which department you want to assign duties for.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {departments.map((dept) => (
              <button
                key={dept.id}
                onClick={() => handleDeptSelect(dept.id)}
                className="p-6 rounded-2xl border-2 border-slate-200 bg-white hover:border-amber-400 hover:bg-amber-50 font-semibold transition flex flex-col text-left"
              >
                <p className="text-lg text-slate-800">{dept.name}</p>
                <p className="text-sm text-slate-500 mt-2">Department Code: {dept.code}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Semester Selection */}
      {currentStep === 2 && (
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-8 shadow-sm border border-white/60 space-y-6 min-h-[400px] flex flex-col justify-center">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-amber-600 mb-2">Page 2: Semester</p>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">Choose Semester</h3>
            <p className="text-slate-600 mb-8">
              For <span className="font-semibold text-amber-600">{selectedDeptData?.name}</span>
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {semesters.map((sem) => (
              <button
                key={sem}
                onClick={() => handleSemSelect(sem)}
                className="p-8 rounded-2xl border-2 border-slate-200 bg-white hover:border-amber-400 hover:bg-amber-50 font-semibold transition text-center"
              >
                <p className="text-3xl text-amber-600 mb-2">{sem}</p>
                <p className="text-sm text-slate-500">Semester</p>
              </button>
            ))}
          </div>

          <div className="flex justify-start pt-6">
            <button
              onClick={handleBackToDept}
              className="px-6 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-100 transition"
            >
              ← Back to Departments
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Subject Selection */}
      {currentStep === 3 && (
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-8 shadow-sm border border-white/60 space-y-6 min-h-[400px] flex flex-col justify-center">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-amber-600 mb-2">Page 3: Subject</p>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">Choose Subject</h3>
            <p className="text-slate-600 mb-2">
              <span className="font-semibold text-amber-600">{selectedDeptData?.name}</span> | Semester <span className="font-semibold text-amber-600">{selectedSem}</span>
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {deptSubjects.map((subject) => (
              <button
                key={subject.id}
                onClick={() => handleSubjectSelect(subject.id)}
                className="p-6 rounded-2xl border-2 border-slate-200 bg-white hover:border-amber-400 hover:bg-amber-50 font-semibold transition flex flex-col text-left"
              >
                <p className="text-lg text-slate-800">{subject.name}</p>
              </button>
            ))}
          </div>

          <div className="flex justify-start pt-6">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-6 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-100 transition"
            >
              ← Back to Semester
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Moderator & Setter Selection */}
      {currentStep === 4 && (
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-8 shadow-sm border border-white/60 space-y-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-amber-600 mb-2">Page 4: Role Assignment</p>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">Assign Moderator & Setter</h3>
            <p className="text-slate-600 mb-6">
              <span className="font-semibold text-amber-600">{selectedDeptData?.name}</span> | Sem {selectedSem} | {selectedSubjectData?.name}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Paper Setter */}
            <div className="space-y-4">
              <h4 className="text-lg font-bold text-slate-800">Paper Setter</h4>
              {!showOtherFacultyPicker.includes('setter') ? (
                <select
                  value={selectedPaperSetter}
                  onChange={(e) => {
                    if (e.target.value === 'other') {
                      setShowOtherFacultyPicker('setter');
                    } else {
                      handleSetterSelect(e.target.value);
                    }
                  }}
                  className="w-full p-3 rounded-xl border border-slate-200 bg-white outline-none focus:ring-2 focus:ring-amber-400"
                >
                  <option value="">Choose faculty...</option>
                  {deptFaculty.map((faculty) => (
                    <option key={faculty} value={faculty}>
                      {faculty}
                    </option>
                  ))}
                  <option value="other">Other (from all faculties)</option>
                </select>
              ) : (
                <div className="space-y-2">
                  <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                    {deptFaculty.map((faculty) => (
                      <button
                        key={faculty}
                        onClick={() => handleSetterSelect(faculty)}
                        className="p-3 rounded-lg border border-slate-200 bg-white text-left hover:border-amber-400 hover:bg-amber-50 transition"
                      >
                        <p className="text-sm font-medium text-slate-800">{faculty}</p>
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setShowOtherFacultyPicker('')}
                    className="w-full p-2 text-sm text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-100 transition"
                  >
                    Back to Dropdown
                  </button>
                </div>
              )}
              {selectedPaperSetter && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
                  <p className="text-sm text-amber-900">
                    <span className="font-bold">Selected:</span> {selectedPaperSetter}
                  </p>
                </div>
              )}
            </div>

            {/* Moderator */}
            <div className="space-y-4">
              <h4 className="text-lg font-bold text-slate-800">Moderator</h4>
              {!showOtherFacultyPicker.includes('moderator') ? (
                <select
                  value={selectedModerator}
                  onChange={(e) => {
                    if (e.target.value === 'other') {
                      setShowOtherFacultyPicker('moderator');
                    } else {
                      handleModeratorSelect(e.target.value);
                    }
                  }}
                  className="w-full p-3 rounded-xl border border-slate-200 bg-white outline-none focus:ring-2 focus:ring-amber-400"
                >
                  <option value="">Choose faculty...</option>
                  {deptFaculty.map((faculty) => (
                    <option key={faculty} value={faculty}>
                      {faculty}
                    </option>
                  ))}
                  <option value="other">Other (from all faculties)</option>
                </select>
              ) : (
                <div className="space-y-2">
                  <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                    {deptFaculty.map((faculty) => (
                      <button
                        key={faculty}
                        onClick={() => handleModeratorSelect(faculty)}
                        className="p-3 rounded-lg border border-slate-200 bg-white text-left hover:border-amber-400 hover:bg-amber-50 transition"
                      >
                        <p className="text-sm font-medium text-slate-800">{faculty}</p>
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setShowOtherFacultyPicker('')}
                    className="w-full p-2 text-sm text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-100 transition"
                  >
                    Back to Dropdown
                  </button>
                </div>
              )}
              {selectedModerator && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                  <p className="text-sm text-emerald-900">
                    <span className="font-bold">Selected:</span> {selectedModerator}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-between pt-6 border-t border-slate-200">
            <button
              onClick={() => setCurrentStep(3)}
              className="px-6 py-2 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-100 transition"
            >
              ← Back to Subject
            </button>
            <button
              onClick={handleCompleteAssignment}
              disabled={!selectedPaperSetter || !selectedModerator}
              className="px-6 py-2 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Complete Assignment ✓
            </button>
          </div>
        </div>
      )}
        </motion.div>
      )}


    </section>
  );
}

function AIMonitoring() {
  const pieData = [
    { name: 'Questions Unchanged', value: 70 },
    { name: 'Questions Edited', value: 20 },
    { name: 'Questions Rejected', value: 10 },
  ];
  const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">AI Performance & Monitoring</h2>
          <p className="text-sm text-slate-500">Track quality, biases, and acceptance rates of generated questions.</p>
        </div>
        <span className="px-3 py-1 bg-emerald-100 text-emerald-700 font-bold text-xs uppercase tracking-wider rounded-lg border border-emerald-200">
          System Healthy
        </span>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
          <h3 className="text-base font-bold text-slate-800">Generation Acceptance</h3>
          <div className="h-48 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs font-medium text-slate-600 mt-2">
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-500"></div> Approved</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-amber-500"></div> Edited</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-rose-500"></div> Rejected</span>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
           <h3 className="text-base font-bold text-slate-800 mb-4">AI Model Health Log</h3>
           <div className="space-y-4">
             <div className="p-4 rounded-xl border border-amber-200 bg-amber-50 flex gap-4">
                <Wand2 className="h-5 w-5 text-amber-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold text-amber-900">Bloom's Distribution Anomaly</h4>
                  <p className="text-xs text-amber-700 mt-1">
                    The latest batch for DBMS skewed heavily towards 'Remember' (45%). Standard config expects max 30%.
                  </p>
                </div>
             </div>
             <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex gap-4">
                <ShieldCheck className="h-5 w-5 text-emerald-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold text-slate-800">Duplicate Check Passed</h4>
                  <p className="text-xs text-slate-500 mt-1">
                    0 duplicates found against the last 5 years of repository papers.
                  </p>
                </div>
             </div>
           </div>
        </div>
      </div>
    </section>
  );
}

function ApprovalWorkflow() {
  const steps = [
    { title: 'Generate Draft', owner: 'Paper Setter', status: 'Complete' },
    { title: 'Auto Validation', owner: 'AI Engine', status: 'Complete' },
    { title: 'Faculty Review', owner: 'Faculty Reviewer', status: 'In Review' },
    { title: 'Final Approval', owner: 'Admin', status: 'Pending' }
  ];

  const queue = [
    { paper: 'DBMS Midterm', stage: 'Faculty Review', eta: '2 hrs', priority: 'High' },
    { paper: 'OS Unit Test 2', stage: 'Auto Validation', eta: '15 min', priority: 'Medium' },
    { paper: 'AI Foundations', stage: 'Final Approval', eta: 'Today', priority: 'Low' }
  ];

  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">Approval Workflow</h2>
        <p className="text-sm text-slate-500">Track progress from paper generation through final approval.</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-4">
        {steps.map((step, i) => (
          <div key={i} className="bg-white/80 backdrop-blur-md rounded-2xl p-5 shadow-sm border border-white/60">
            <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide">Step {i + 1}</p>
            <h3 className="text-base font-bold text-slate-800 mt-2">{step.title}</h3>
            <p className="text-xs text-slate-500 mt-1">Owner: {step.owner}</p>
            <span className={`inline-flex mt-3 px-2.5 py-1 rounded-lg text-xs font-semibold ${
              step.status === 'Complete'
                ? 'bg-emerald-100 text-emerald-700'
                : step.status === 'In Review'
                ? 'bg-amber-100 text-amber-700'
                : 'bg-slate-100 text-slate-600'
            }`}>
              {step.status}
            </span>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
          <h3 className="text-lg font-bold text-slate-800 mb-4">Active Review Queue</h3>
          <div className="space-y-3">
            {queue.map((item, i) => (
              <div key={i} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-slate-800">{item.paper}</p>
                  <p className="text-xs text-slate-500">Stage: {item.stage}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-semibold text-slate-700">ETA: {item.eta}</p>
                  <span className={`inline-flex mt-1 px-2 py-0.5 rounded-md text-xs font-semibold ${
                    item.priority === 'High'
                      ? 'bg-rose-100 text-rose-700'
                      : item.priority === 'Medium'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-emerald-100 text-emerald-700'
                  }`}>
                    {item.priority}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
          <h3 className="text-lg font-bold text-slate-800">SLA Compliance</h3>
          <p className="text-xs text-slate-500 mt-1">Average approval time last 30 days.</p>
          <div className="mt-6 space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                <span>Draft to Review</span>
                <span>6.4 hrs</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-slate-100">
                <div className="h-2 rounded-full bg-emerald-400" style={{ width: '72%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                <span>Review to Approval</span>
                <span>12.1 hrs</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-slate-100">
                <div className="h-2 rounded-full bg-amber-400" style={{ width: '54%' }}></div>
              </div>
            </div>
            <button className="w-full mt-2 rounded-xl bg-slate-900 text-white text-sm font-semibold py-2.5 hover:bg-slate-800 transition">
              View Workflow Report
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

type FinalizedPaperRecord = {
  course: string;
  semester: string;
  subject: string;
  code: string;
  reviewer: string;
  feedback: string;
  approvedAt: string;
};

interface UploadedPaperRecord {
  paper_id: number;
  filename: string;
  subject: string;
  subject_code: string;
  branch: string;
  semester: string;
  exam_type: string;
  exam_year?: number;
  exam_date?: string;
  upload_date?: string;
  total_questions?: number;
}

function FinalizedPapers() {
  const [papers, setPapers] = useState<UploadedPaperRecord[]>([]);
  const [printStatus, setPrintStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPaper, setSelectedPaper] = useState<any | null>(null);
  const [paperModalOpen, setPaperModalOpen] = useState(false);

  useEffect(() => {
    const loadPapers = async () => {
      setLoading(true);
      try {
        const token = sessionStorage.getItem('adminToken');
        if (!token) {
          setPapers([]);
          return;
        }

        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/uploaded-papers?limit=100`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setPapers(data.papers || []);
        }
      } catch (error) {
        console.error('Failed to load papers:', error);
        setPapers([]);
      } finally {
        setLoading(false);
      }
    };

    loadPapers();
  }, []);

  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Uploaded Question Papers</h2>
          <p className="text-sm text-slate-500">OCR-extracted question papers stored in the database with all metadata.</p>
        </div>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">
          {papers.length} uploaded
        </span>
      </div>

      {loading ? (
        <div className="rounded-2xl bg-white/80 backdrop-blur-md border border-white/60 px-6 py-10 text-center text-slate-500">
          Loading papers...
        </div>
      ) : papers.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white/80 p-10 text-center shadow-sm">
          <FileCheck className="mx-auto h-12 w-12 text-slate-300" />
          <h3 className="mt-4 text-lg font-bold text-slate-800">No papers uploaded yet</h3>
          <p className="mt-2 text-sm text-slate-500">Upload question papers using the OCR extractor to see them here.</p>
        </div>
      ) : (
        <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-slate-500 bg-slate-50/70">
              <tr>
                <th className="px-6 py-4 font-medium">Subject</th>
                <th className="px-6 py-4 font-medium">Code</th>
                <th className="px-6 py-4 font-medium">Branch</th>
                <th className="px-6 py-4 font-medium">Semester</th>
                <th className="px-6 py-4 font-medium">Questions</th>
                <th className="px-6 py-4 font-medium">Upload Date</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {papers.map((paper) => (
                <tr key={paper.paper_id} className="hover:bg-slate-50/50 transition">
                  <td className="px-6 py-4 font-semibold text-slate-800">{paper.subject}</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-md bg-blue-100 border border-blue-200 text-xs font-semibold text-blue-700">
                      {paper.subject_code || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-600">{paper.branch}</td>
                  <td className="px-6 py-4 text-slate-600">Sem {paper.semester}</td>
                  <td className="px-6 py-4">
                    <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold">
                      {paper.total_questions || 0}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-600">
                    {paper.upload_date ? new Date(paper.upload_date).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={async () => {
                        const token = sessionStorage.getItem('adminToken');
                        if (!token) return;
                        try {
                          const resp = await fetch(`${API_CONFIG.BACKEND_URL}/api/papers/${paper.paper_id}`, {
                            headers: { Authorization: `Bearer ${token}` }
                          });
                          if (!resp.ok) {
                            console.error('Failed to fetch paper details');
                            return;
                          }
                          const data = await resp.json();
                          setSelectedPaper(data.paper || data.paper || null);
                          setPaperModalOpen(true);
                        } catch (e) {
                          console.error('Error loading paper details', e);
                        }
                      }}
                      className="text-amber-600 hover:text-orange-700 font-medium text-sm"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {/* Paper Details Modal */}
      {paperModalOpen && selectedPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-3xl bg-white rounded-xl p-6 shadow-lg">
            <div className="flex items-start justify-between">
              <h3 className="text-lg font-bold">Paper Details</h3>
              <button onClick={() => { setPaperModalOpen(false); setSelectedPaper(null); }} className="text-sm text-slate-500">Close</button>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-3 text-sm text-slate-700">
              <div><strong>Subject:</strong> {selectedPaper.subject}</div>
              <div><strong>Subject Code:</strong> {selectedPaper.subject_code}</div>
              <div><strong>Branch:</strong> {selectedPaper.branch}</div>
              <div><strong>Semester:</strong> {selectedPaper.semester}</div>
              <div><strong>Uploaded:</strong> {selectedPaper.upload_date || 'N/A'}</div>
              <div><strong>Total Questions:</strong> {selectedPaper.total_questions || 0}</div>
              <div className="mt-3">
                <h4 className="font-semibold">OCR Preview / Notes</h4>
                <pre className="max-h-64 overflow-auto p-3 bg-slate-50 rounded-md text-xs">{selectedPaper.ocr_text || selectedPaper.preview || JSON.stringify(selectedPaper, null, 2)}</pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function ReportsAnalytics() {
  const barData = [
    { name: 'CSE', papers: 420, approvals: 380 },
    { name: 'ECE', papers: 310, approvals: 265 },
    { name: 'ME', papers: 220, approvals: 200 },
    { name: 'MBA', papers: 180, approvals: 150 },
    { name: 'Math', papers: 140, approvals: 120 }
  ];

  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Reports & Analytics</h2>
          <p className="text-sm text-slate-500">Departmental output, quality trends, and reviewer performance.</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-2 text-xs font-semibold rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900">Export CSV</button>
          <button className="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-900 text-white">Download Report</button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60">
          <h3 className="text-lg font-bold text-slate-800 mb-4">Department Output</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} barSize={22}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="papers" fill="#f59e0b" radius={[12, 12, 0, 0]} />
                <Bar dataKey="approvals" fill="#0ea5e9" radius={[12, 12, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60 space-y-4">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Quality Snapshot</h3>
            <p className="text-xs text-slate-500">Top KPIs for this month.</p>
          </div>
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-xs text-slate-500">Reviewer Turnaround</p>
              <p className="text-xl font-bold text-slate-800">8.2 hrs</p>
              <p className="text-xs text-emerald-600">-12% vs last month</p>
            </div>
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-xs text-slate-500">Revision Rate</p>
              <p className="text-xl font-bold text-slate-800">18.4%</p>
              <p className="text-xs text-rose-600">+3.2% vs last month</p>
            </div>
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-xs text-slate-500">AI Accuracy</p>
              <p className="text-xl font-bold text-slate-800">94.7%</p>
              <p className="text-xs text-emerald-600">+0.5% vs last month</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function SystemSettings() {
  return (
    <section className="px-4 py-8 md:px-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">System Settings</h2>
        <p className="text-sm text-slate-500">Control access, notifications, and AI policy defaults.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60 space-y-5">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Access Control</h3>
            <p className="text-xs text-slate-500">Manage roles and multi-factor authentication.</p>
          </div>
          <div className="space-y-4 text-sm">
            <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4">
              <div>
                <p className="font-semibold text-slate-800">MFA Enforcement</p>
                <p className="text-xs text-slate-500">Require MFA for all admin accounts.</p>
              </div>
              <input type="checkbox" className="h-5 w-5 accent-amber-500" defaultChecked />
            </div>
            <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4">
              <div>
                <p className="font-semibold text-slate-800">Role Auto Sync</p>
                <p className="text-xs text-slate-500">Sync faculty roles from SIS nightly.</p>
              </div>
              <input type="checkbox" className="h-5 w-5 accent-amber-500" />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Default Reviewer Level</label>
              <select className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none">
                <option>Senior Faculty Reviewer</option>
                <option>Faculty Reviewer</option>
                <option>Assistant Faculty Reviewer</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-sm border border-white/60 space-y-5">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Notifications</h3>
            <p className="text-xs text-slate-500">Fine-tune alerts and approval reminders.</p>
          </div>
          <div className="space-y-4 text-sm">
            <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4">
              <div>
                <p className="font-semibold text-slate-800">Escalation Alerts</p>
                <p className="text-xs text-slate-500">Notify admins when approvals exceed SLA.</p>
              </div>
              <input type="checkbox" className="h-5 w-5 accent-amber-500" defaultChecked />
            </div>
            <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4">
              <div>
                <p className="font-semibold text-slate-800">Daily Digest</p>
                <p className="text-xs text-slate-500">Summary of approvals and AI alerts.</p>
              </div>
              <input type="checkbox" className="h-5 w-5 accent-amber-500" defaultChecked />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Notification Channel</label>
              <select className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 outline-none">
                <option>Email + In-app</option>
                <option>In-app only</option>
                <option>Email only</option>
              </select>
            </div>
            <button className="w-full rounded-xl bg-slate-900 text-white text-sm font-semibold py-2.5 hover:bg-slate-800 transition">
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
