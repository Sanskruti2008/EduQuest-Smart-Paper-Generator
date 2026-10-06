import { SplitSquareHorizontal } from 'lucide-react';

export default function ComparisonPanel() {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 overflow-hidden">
      <div className="border-b border-slate-100 px-6 py-4 bg-slate-50/60 flex items-center gap-2">
        <SplitSquareHorizontal className="h-5 w-5 text-amber-600" />
        <h2 className="font-semibold text-slate-800">Side-by-Side Comparison</h2>
      </div>
      <div className="grid md:grid-cols-2 gap-4 p-6">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold text-slate-500 mb-3">Original Draft</p>
          <div className="space-y-4 text-sm text-slate-700">
            <div>
              <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded">Q1. (a)</span>
              <p className="mt-2">Explain SDLC phases and compare Agile with Waterfall.</p>
            </div>
            <div>
              <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded">Q2.</span>
              <p className="mt-2">Describe requirement engineering techniques used in agile teams.</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-xs font-semibold text-amber-700 mb-3">Suggested Corrections</p>
          <div className="space-y-4 text-sm text-slate-800">
            <div>
              <span className="font-mono text-xs bg-white px-2 py-1 rounded">Q1. (a)</span>
              <p className="mt-2">
                Explain SDLC phases and <span className="bg-white/80 px-1 rounded">contrast Agile and Waterfall models with two examples</span>.
              </p>
            </div>
            <div>
              <span className="font-mono text-xs bg-white px-2 py-1 rounded">Q2.</span>
              <p className="mt-2">Discuss agile requirement gathering with user stories and backlog grooming.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
