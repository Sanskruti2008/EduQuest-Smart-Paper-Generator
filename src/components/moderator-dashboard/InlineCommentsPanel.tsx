import { MessageSquareDiff } from 'lucide-react';

export type InlineIssue = {
  id: string;
  label: string;
  marks: string;
  level: string;
  text: string;
  highlight: string;
  comment: string;
};

type InlineCommentsPanelProps = {
  issues: InlineIssue[];
  onUpdateComment: (issueId: string, comment: string) => void;
};

export default function InlineCommentsPanel({
  issues,
  onUpdateComment
}: InlineCommentsPanelProps) {
  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-sm border border-white/60 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-800">Inline Comments</h3>
        <span className="text-xs font-semibold text-slate-500">{issues.length} highlights</span>
      </div>
      <div className="space-y-4">
        {issues.map((issue) => (
          <div key={issue.id} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-amber-600">{issue.label}</span>
              <span className="text-xs text-slate-500">{issue.marks} • {issue.level}</span>
            </div>
            <p className="text-sm text-slate-700">
              {issue.text}{' '}
              <span className="bg-amber-100 px-1 rounded">{issue.highlight}</span>
            </p>
            <div className="mt-3 bg-slate-50 p-3 rounded-lg border border-slate-200 flex items-start gap-3">
              <MessageSquareDiff className="h-5 w-5 text-slate-400 mt-0.5" />
              <textarea
                className="flex-1 text-sm bg-white border border-slate-300 rounded p-2 text-slate-600 focus:ring-2 focus:ring-amber-400 outline-none resize-none"
                placeholder="Add inline correction or suggestion for faculty..."
                rows={2}
                value={issue.comment}
                onChange={(event) => onUpdateComment(issue.id, event.target.value)}
              ></textarea>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
