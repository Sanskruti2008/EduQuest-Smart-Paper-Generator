import {
    ChevronLeft,
    ChevronRight,
    ClipboardCheck,
    FileOutput,
    FolderOpen,
    GraduationCap,
    LayoutDashboard,
    LibraryBig,
    ListTodo,
    LogOut
} from 'lucide-react';

const sidebarItems = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'assigned-tasks', label: 'Assigned Tasks', icon: ListTodo },
  { key: 'question-bank', label: 'Question Bank', icon: LibraryBig },
  { key: 'paper-generation', label: 'Paper Generation', icon: FileOutput },
  { key: 'my-papers', label: 'My Papers', icon: FolderOpen },
  { key: 'moderation', label: 'Moderation', icon: ClipboardCheck },
  { key: 'logout', label: 'Logout', icon: LogOut }
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  widthClass: string;
  activeKey: string;
  onSelect: (key: string) => void;
}

export default function Sidebar({ collapsed, onToggle, widthClass, activeKey, onSelect }: SidebarProps) {
  return (
    <aside className={`${widthClass} hidden lg:flex flex-col border-r border-[var(--border)] bg-[var(--surface)] backdrop-blur-xl shadow-xl transition-all duration-300`}>
      <div className="flex items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 text-white flex items-center justify-center shadow-lg">
            <GraduationCap className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div>
              <p className="text-lg font-semibold">EduQuest – Smart Question Paper Generator</p>
              <p className="text-xs text-slate-500">Faculty Console</p>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="hidden lg:flex items-center justify-center h-8 w-8 rounded-xl bg-[var(--surface-2)] shadow-sm hover:shadow-md transition text-[var(--text-muted)]"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex-1 px-3 pb-6">
        <ul className="space-y-2">
          {sidebarItems.map((item) => (
            <li key={item.label}>
              <button
                onClick={() => onSelect(item.key)}
                className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${
                  activeKey === item.key
                    ? 'bg-gradient-to-r from-[var(--accent-from)] to-[var(--accent-to)] text-white shadow-sm'
                    : 'text-slate-700 hover:bg-white/80 hover:text-slate-900'
                }`}
                aria-current={activeKey === item.key ? 'page' : undefined}
                type="button"
              >
                <item.icon className="h-4 w-4" />
                {!collapsed && item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>

    </aside>
  );
}
