import { AlertTriangle, ChevronRight, FileCheck } from 'lucide-react';

type DecisionSummaryPanelProps = {
  status: string;
  highlightCount: number;
  commentCount: number;
  generalComment: string;
  onUpdateGeneralComment: (value: string) => void;
};

export default function DecisionSummaryPanel({
  status,
  highlightCount,
  commentCount,
  generalComment,
  onUpdateGeneralComment
}: DecisionSummaryPanelProps) {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 p-6">
      <h3 className="font-bold text-slate-800 mb-3 flex items-center gap-2">
        <FileCheck className="h-5 w-5 text-emerald-500" /> Decision Summary
      </h3>
      <div className="space-y-2 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" /> {highlightCount} highlighted items require revision
        </div>
        <div className="flex items-center gap-2">
          <ChevronRight className="h-4 w-4 text-slate-400" /> {commentCount} inline comment{commentCount === 1 ? '' : 's'} captured
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
            status === 'Approved'
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : status === 'Rejected'
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : status === 'Needs Corrections'
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-slate-50 text-slate-600 border-slate-200'
          }`}>
            Status: {status}
          </span>
        </div>
      </div>
      <div className="mt-4">
        <label className="text-xs font-semibold text-slate-600">General review note</label>
        <textarea
          className="mt-2 w-full text-sm bg-white border border-slate-200 rounded-lg p-2 text-slate-600 focus:ring-2 focus:ring-amber-400 outline-none resize-none"
          rows={3}
          placeholder="Summarize corrections or rationale for approval/rejection..."
          value={generalComment}
          onChange={(event) => onUpdateGeneralComment(event.target.value)}
        ></textarea>
      </div>
    </div>
  );
}
