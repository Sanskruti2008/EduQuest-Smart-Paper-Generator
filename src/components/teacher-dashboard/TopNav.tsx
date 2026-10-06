import { Bell, LayoutDashboard, Search } from 'lucide-react';
import ThemeToggle from '../ThemeToggle';

interface TopNavProps {
  collapsed: boolean;
  onToggle: () => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export default function TopNav({ collapsed, onToggle }: TopNavProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur-xl shadow-sm">
      <div className="flex flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggle}
            aria-expanded={!collapsed}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="flex lg:hidden items-center justify-center h-10 w-10 rounded-2xl bg-white shadow-sm"
          >
            <LayoutDashboard className="h-5 w-5" />
          </button>
          <div>
            <p className="text-sm text-slate-500">Semester 6 • CSE</p>
            <h1 className="text-xl font-semibold">Teacher Dashboard</h1>
          </div>
        </div>

        <div className="flex flex-1 items-center gap-3 md:justify-end">
          <div className="flex-1 md:max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                placeholder="Search questions, papers, topics"
                className="w-full rounded-2xl border border-[var(--input-border)] bg-[var(--input-bg)] py-2 pl-10 pr-4 text-sm text-[var(--text)] shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
              />
            </div>
          </div>

          <button className="hidden md:flex items-center gap-2 rounded-2xl bg-white px-3 py-2 text-sm shadow-sm">
            <Bell className="h-4 w-4 text-amber-600" />
            Alerts
          </button>

          <ThemeToggle />

          <div className="flex items-center gap-2 rounded-2xl bg-white px-3 py-2 shadow-sm">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-orange-400 to-yellow-400"></div>
            <div className="hidden md:block">
              <p className="text-sm font-semibold">Prof. Aria</p>
              <p className="text-xs text-slate-500">Paper Setter</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
