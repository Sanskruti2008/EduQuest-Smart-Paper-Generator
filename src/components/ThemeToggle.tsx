import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      aria-pressed={isDark}
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] shadow-sm transition-colors duration-200 hover:text-[var(--accent-text)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/30"
    >
      <span className="relative flex h-5 w-5 items-center justify-center">
        <Moon
          className={`absolute h-4 w-4 transition-all duration-200 ${isDark ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'}`}
          aria-hidden="true"
        />
        <Sun
          className={`absolute h-4 w-4 text-[var(--accent-text)] transition-all duration-200 ${isDark ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-0 opacity-0'}`}
          aria-hidden="true"
        />
      </span>
    </button>
  );
}
