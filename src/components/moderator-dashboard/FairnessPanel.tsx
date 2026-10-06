import { UserRoundCheck } from 'lucide-react';

export default function FairnessPanel() {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 p-6">
      <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
        <UserRoundCheck className="h-5 w-5 text-emerald-500" /> Fairness Validation
      </h3>
      <div className="space-y-3 text-sm">
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3">
          <span className="text-slate-600">Bloom's Distribution</span>
          <span className="text-emerald-600 font-semibold">Aligned</span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3">
          <span className="text-slate-600">Repeated Questions</span>
          <span className="text-emerald-600 font-semibold">0 Found</span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-amber-100 bg-amber-50 p-3">
          <span className="text-slate-700">Coverage Gaps</span>
          <span className="text-amber-700 font-semibold">Unit 4 missing</span>
        </div>
      </div>
    </div>
  );
}
