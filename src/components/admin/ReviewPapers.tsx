import { useEffect, useState } from 'react';
import { API_CONFIG } from '../../utils/constants';

type ReviewPaper = {
  paper_id: number;
  subject_name: string;
  subject_code: string;
  exam_type: string;
  exam_year: number | null;
  created_at: string;
  generated_by_name: string;
  moderated_by_name: string | null;
  status: string;
  moderation_comments: string | null;
  review_comments: string | null;
  sections: Record<string, { questions?: Array<{ question_text?: string; marks?: number }> }>;
};

export default function ReviewPapers() {
  const [papers, setPapers] = useState<ReviewPaper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedPaper, setSelectedPaper] = useState<ReviewPaper | null>(null);
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);

  const loadPapers = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = sessionStorage.getItem('adminToken');
      if (!token) throw new Error('Admin session expired. Please sign in again.');
      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/admin/review-papers`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok || !data.success || !Array.isArray(data.papers)) {
        throw new Error(data.message || 'Unable to load papers for admin review.');
      }
      setPapers(data.papers);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load papers for admin review.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadPapers(); }, []);

  const finalizePaper = async () => {
    if (!selectedPaper) return;
    setSaving(true);
    setError(null);
    try {
      const token = sessionStorage.getItem('adminToken');
      if (!token) throw new Error('Admin session expired. Please sign in again.');
      const response = await fetch(
        `${API_CONFIG.BACKEND_URL}/api/admin/review-papers/${selectedPaper.paper_id}/finalize`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ comment }),
        },
      );
      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Unable to finalize this paper.');
      }
      setPapers(current => current.filter(paper => paper.paper_id !== selectedPaper.paper_id));
      setSelectedPaper(null);
      setComment('');
      setNotice('Paper finalized successfully.');
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to finalize this paper.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6 px-4 py-8 md:px-8">
      <header>
        <h2 className="text-2xl font-bold text-slate-800">Review Papers</h2>
        <p className="mt-1 text-sm text-slate-500">Papers appear here only after moderator approval.</p>
      </header>
      {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {notice && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}

      {loading ? <p className="rounded-2xl bg-white/80 p-8 text-center text-sm text-slate-500">Loading papers for review...</p>
        : papers.length === 0 ? <p className="rounded-2xl border border-dashed border-slate-300 bg-white/80 p-8 text-center text-sm text-slate-500">No moderator-approved papers are awaiting admin review.</p>
          : (
            <div className="overflow-x-auto rounded-2xl border border-white/60 bg-white/80 shadow-sm">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="border-b border-slate-100 bg-slate-50/70 text-slate-500">
                  <tr>
                    <th className="px-5 py-4 font-medium">Subject</th>
                    <th className="px-5 py-4 font-medium">Exam</th>
                    <th className="px-5 py-4 font-medium">Paper Setter</th>
                    <th className="px-5 py-4 font-medium">Moderator</th>
                    <th className="px-5 py-4 font-medium">Status</th>
                    <th className="px-5 py-4 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {papers.map(paper => (
                    <tr key={paper.paper_id}>
                      <td className="px-5 py-4 font-semibold text-slate-800">{paper.subject_name}<span className="block text-xs font-normal text-slate-500">{paper.subject_code}</span></td>
                      <td className="px-5 py-4 text-slate-600">{paper.exam_type} {paper.exam_year || ''}</td>
                      <td className="px-5 py-4 text-slate-600">{paper.generated_by_name}</td>
                      <td className="px-5 py-4 text-slate-600">{paper.moderated_by_name || '—'}</td>
                      <td className="px-5 py-4 text-slate-600">{paper.status.replace(/_/g, ' ')}</td>
                      <td className="px-5 py-4 text-right">
                        <button type="button" onClick={() => { setSelectedPaper(paper); setComment(''); }} className="rounded-lg bg-amber-600 px-3 py-2 text-xs font-semibold text-white">Review</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

      {selectedPaper && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div role="dialog" aria-modal="true" aria-labelledby="admin-review-title" className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 id="admin-review-title" className="text-xl font-bold text-slate-800">{selectedPaper.subject_name} — {selectedPaper.exam_type} {selectedPaper.exam_year || ''}</h3>
                <p className="mt-1 text-sm text-slate-500">Paper setter: {selectedPaper.generated_by_name} · Moderator: {selectedPaper.moderated_by_name || 'Unknown'}</p>
              </div>
              <button type="button" onClick={() => setSelectedPaper(null)} className="text-sm text-slate-500">Close</button>
            </div>
            {selectedPaper.moderation_comments && <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">Moderator comment: {selectedPaper.moderation_comments}</p>}
            <div className="mt-4 space-y-4">
              {Object.entries(selectedPaper.sections || {}).map(([section, data]) => (
                <div key={section}>
                  <h4 className="font-semibold text-slate-700">{section}</h4>
                  <ol className="mt-2 list-decimal space-y-2 pl-5 text-sm text-slate-700">
                    {(data.questions || []).map((question, index) => (
                      <li key={`${section}-${index}`}>{question.question_text || 'Question text unavailable'} <span className="text-slate-500">({question.marks ?? '—'} marks)</span></li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
            <label className="mt-5 block text-sm font-semibold text-slate-700">
              Admin review comment
              <textarea value={comment} onChange={event => setComment(event.target.value)} rows={3} className="mt-2 w-full rounded-xl border border-slate-200 p-3 font-normal" placeholder="Optional comment for the paper setter" />
            </label>
            <button type="button" onClick={() => void finalizePaper()} disabled={saving} className="mt-4 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
              {saving ? 'Finalizing...' : 'Finalize Paper'}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
