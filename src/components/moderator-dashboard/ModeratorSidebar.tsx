import { Search, ShieldCheck } from 'lucide-react';

export type ModeratorPaper = {
  title: string;
  code: string;
  dept: string;
  status: string;
  due: string;
};

type ModeratorSidebarProps = {
  papers: ModeratorPaper[];
  activePaper: number;
  onSelectPaper: (index: number) => void;
};

export default function ModeratorSidebar({
  papers,
  activePaper,
  onSelectPaper
}: ModeratorSidebarProps) {
  return (
    <aside className="hidden lg:flex w-72 flex-col border-r border-white/40 bg-white/60 backdrop-blur-xl shadow-xl">
      <div className="px-6 py-6 flex items-center gap-3">
        <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 text-white flex items-center justify-center shadow-lg">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <p className="text-lg font-bold text-slate-800">EduQuest</p>
          <p className="text-xs font-semibold text-amber-600 tracking-wide uppercase">Faculty Reviewer</p>
        </div>
      </div>

      <div className="px-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            placeholder="Search papers..."
            className="w-full rounded-2xl border border-white/60 bg-white/80 py-2 pl-10 pr-4 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent transition-all"
          />
        </div>
      </div>

      <div className="px-4 py-6 space-y-3 overflow-y-auto">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-2">Assigned Papers</p>
        {papers.map((paper, index) => (
          <button
            key={paper.code}
            onClick={() => onSelectPaper(index)}
            className={`w-full text-left rounded-2xl border px-4 py-3 transition ${
              activePaper === index
                ? 'bg-gradient-to-r from-amber-400 to-orange-500 text-white border-transparent shadow-md'
                : 'bg-white/70 border-white/60 text-slate-700 hover:bg-white'
            }`}
          >
            <p className="text-sm font-semibold">{paper.title}</p>
            <p className={`text-xs ${activePaper === index ? 'text-white/80' : 'text-slate-500'}`}>
              {paper.code} • {paper.dept}
            </p>
            <p className={`text-xs mt-2 ${activePaper === index ? 'text-white/80' : 'text-amber-600'}`}>
              {paper.status}
            </p>
          </button>
        ))}
      </div>
    </aside>
  );
}
