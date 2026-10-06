import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

const analyticsData = [
  { name: 'Jan', papers: 12, accuracy: 88 },
  { name: 'Feb', papers: 18, accuracy: 90 },
  { name: 'Mar', papers: 24, accuracy: 91 },
  { name: 'Apr', papers: 20, accuracy: 93 },
  { name: 'May', papers: 28, accuracy: 92 },
  { name: 'Jun', papers: 32, accuracy: 94 }
];

const difficultyData = [
  { name: 'Easy', value: 35 },
  { name: 'Medium', value: 45 },
  { name: 'Hard', value: 20 }
];

const subjectDistribution = [
  { name: 'DBMS', value: 32 },
  { name: 'OS', value: 24 },
  { name: 'SE', value: 18 },
  { name: 'CN', value: 14 },
  { name: 'AI', value: 12 }
];

const progressData = [
  { name: 'Week 1', papers: 6 },
  { name: 'Week 2', papers: 12 },
  { name: 'Week 3', papers: 18 },
  { name: 'Week 4', papers: 22 }
];

const palette = ['#F59E0B', '#F97316', '#FDBA74', '#FBBF24', '#FDE68A'];

export default function TeacherDashboardAnalytics() {
  return (
    <section id="analytics" className="px-4 pb-12 md:px-8">
      <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Analytics</h3>
          <span className="text-xs text-slate-500">Updated today</span>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-700">Paper Generation Trend</p>
            <div className="mt-4 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analyticsData}>
                  <defs>
                    <linearGradient id="papersGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="papers" stroke="#F59E0B" fill="url(#papersGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-700">Subject Distribution</p>
            <div className="mt-4 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={subjectDistribution} dataKey="value" nameKey="name" innerRadius={35} outerRadius={60} paddingAngle={3}>
                    {subjectDistribution.map((entry, index) => (
                      <Cell key={entry.name} fill={palette[index % palette.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-700">Difficulty Analysis</p>
            <div className="mt-4 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={difficultyData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#F97316" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-700">Faculty Activity</p>
            <div className="mt-4 h-36">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={progressData}>
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="papers" stroke="#F59E0B" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-700">AI Accuracy Metrics</p>
            <div className="mt-4 h-36">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analyticsData}>
                  <defs>
                    <linearGradient id="accuracyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#F97316" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#F97316" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="accuracy" stroke="#F97316" fill="url(#accuracyGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
