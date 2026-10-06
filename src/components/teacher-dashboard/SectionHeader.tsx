import type { ComponentType } from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle: string;
  icon: ComponentType<{ className?: string }>;
}

export default function SectionHeader({ title, subtitle, icon: Icon }: SectionHeaderProps) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold text-amber-700">
          <Icon className="h-4 w-4" />
          {title}
        </div>
        <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
      </div>
    </div>
  );
}
