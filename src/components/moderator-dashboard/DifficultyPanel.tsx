import { Scale } from 'lucide-react';

export default function DifficultyPanel() {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 p-6">
      <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
        <Scale className="h-5 w-5 text-amber-500" /> Difficulty Balancing
      </h3>
      <p className="text-xs text-slate-500 mb-3">Target distribution: 30% Easy, 40% Medium, 30% Hard</p>
      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden flex">
        <div className="bg-emerald-400 h-full" style={{ width: '28%' }}></div>
        <div className="bg-amber-400 h-full" style={{ width: '44%' }}></div>
        <div className="bg-rose-400 h-full" style={{ width: '28%' }}></div>
      </div>
      <div className="flex justify-between text-xs text-slate-500 mt-2">
        <span>28% Easy</span>
        <span>44% Medium</span>
        <span>28% Hard</span>
      </div>
    </div>
  );
}
