import { ClipboardList } from 'lucide-react';

export default function ChecklistPanel() {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 p-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-slate-800 flex items-center gap-2">
          <ClipboardList className="h-5 w-5 text-amber-500" /> Moderation Checklist
        </h3>
        <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">2/5</span>
      </div>
      <div className="space-y-3 text-sm">
        <label className="flex items-start gap-3 cursor-pointer p-2 hover:bg-slate-50 rounded transition">
          <input type="checkbox" className="mt-1 rounded text-amber-600 focus:ring-amber-500" defaultChecked />
          <span className="text-slate-600">Syllabus coverage is complete</span>
        </label>
        <label className="flex items-start gap-3 cursor-pointer p-2 hover:bg-slate-50 rounded transition">
          <input type="checkbox" className="mt-1 rounded text-amber-600 focus:ring-amber-500" defaultChecked />
          <span className="text-slate-600">Questions are unambiguous</span>
        </label>
        <label className="flex items-start gap-3 cursor-pointer p-2 hover:bg-slate-50 rounded transition">
          <input type="checkbox" className="mt-1 rounded text-amber-600 focus:ring-amber-500" />
          <span className="text-slate-600">Marks align with complexity</span>
        </label>
        <label className="flex items-start gap-3 cursor-pointer p-2 hover:bg-slate-50 rounded transition">
          <input type="checkbox" className="mt-1 rounded text-amber-600 focus:ring-amber-500" />
          <span className="text-slate-600">Difficulty is balanced across sections</span>
        </label>
        <label className="flex items-start gap-3 cursor-pointer p-2 hover:bg-slate-50 rounded transition">
          <input type="checkbox" className="mt-1 rounded text-amber-600 focus:ring-amber-500" />
          <span className="text-slate-600">No bias or repetition detected</span>
        </label>
      </div>
    </div>
  );
}
