import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { API_CONFIG } from '../utils/constants';
import { clearReviewData, readReviewData } from '../utils/reviewData';

const ReviewExtracted: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [data, setData] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const resolveData = () => {
      const routedData = (location.state as any)?.extractedData;
      if (routedData) return routedData;
      return readReviewData();
    };

    const resolved = resolveData();
    if (!resolved) {
      setData(null);
      return;
    }

    const normalized = resolved.papers ? resolved : resolved.extracted_data || resolved.data || null;
    if (!normalized || !Array.isArray(normalized.papers)) {
      setData(null);
      return;
    }

    setData(normalized);
  }, [location.state, navigate]);

  const updateQuestionField = (pIdx: number, qIdx: number, field: string, value: any) => {
    setData((prev: any) => {
      const copy = JSON.parse(JSON.stringify(prev));
      copy.papers[pIdx].questions[qIdx][field] = value;
      return copy;
    });
  };

  const addQuestion = (pIdx: number) => {
    setData((prev: any) => {
      const copy = JSON.parse(JSON.stringify(prev));
      const paper = copy.papers[pIdx] || { questions: [] };
      const newQ = { question_number: String((paper.questions?.length || 0) + 1), question_text: '', marks: 0, course_outcome: '', has_math: false, sub_questions: [] };
      paper.questions = paper.questions || [];
      paper.questions.push(newQ);
      copy.papers[pIdx] = paper;
      return copy;
    });
  };

  const renumberPaperQuestions = (papers: any[], pIdx: number) => {
    const copy = JSON.parse(JSON.stringify(papers));
    const qs = copy[pIdx].questions || [];
    let seq = 1;
    for (let i = 0; i < qs.length; i++) {
      qs[i].question_number = String(seq);
      seq += 1;
    }
    return copy;
  };

  const deleteQuestion = (pIdx: number, qIdx: number) => {
    if (!confirm('Delete this question?')) return;
    setData((prev: any) => {
      const copy = JSON.parse(JSON.stringify(prev));
      copy.papers[pIdx].questions.splice(qIdx, 1);
      copy.papers = renumberPaperQuestions(copy.papers, pIdx);
      return copy;
    });
  };

  const handleSaveToDb = async () => {
    if (!data) return;
    setSaving(true);
    try {
      const token = sessionStorage.getItem('adminToken') || sessionStorage.getItem('authToken');
      const examInfo = {
        ...(data?.exam_info || {}),
        subject_name: (data?.exam_info?.subject_name || data?.exam_info?.subject || '').trim(),
        subject_code: (data?.exam_info?.subject_code || '').trim(),
        branch: (data?.exam_info?.branch || '').trim(),
        semester: (data?.exam_info?.semester || '').trim(),
      };

      const body = {
        json_file: data.json_file || '',
        branch: examInfo.branch || '',
        semester: examInfo.semester || '',
        subject: examInfo.subject_name || '',
        subject_code: examInfo.subject_code || '',
        papers_data: data.papers,
        exam_info: examInfo,
      };
      if (!token) {
        alert('Login required to save. Please sign in and try again.');
        setSaving(false);
        return;
      }

      const resp = await fetch(`${API_CONFIG.BACKEND_URL}/api/save-extracted-paper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
        body: JSON.stringify(body),
      });
      const d = await resp.json();
      if (resp.ok) {
        clearReviewData();
        const similarity = d.similarity;
        if (similarity?.status === 'completed') {
          alert(
            `Saved to DB and similarity processing completed.\n` +
            `${similarity.processed} processed, ${similarity.duplicates} duplicates, ` +
            `${similarity.new_questions} new canonical questions.`
          );
        } else if (similarity?.status === 'failed') {
          alert(
            `Saved to DB, but similarity processing failed: ${similarity.error || 'Unknown error'}`
          );
        } else {
          alert('Saved to DB');
        }
        navigate('/ocr-upload');
      } else {
        alert('Save failed: ' + (d.error || 'Unknown'));
      }
    } catch (e) {
      console.error(e);
      alert('Network error while saving');
    } finally {
      setSaving(false);
    }
  };

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="p-6 max-w-6xl mx-auto">
          <div className="bg-white rounded shadow-sm p-8 text-center">
            <h1 className="text-2xl font-bold mb-3">Review Extracted Questions</h1>
            <p className="text-gray-600 mb-4">No extracted questions were found to review.</p>
            <button onClick={() => navigate('/ocr-upload')} className="px-4 py-2 bg-blue-600 text-white rounded">Go back to upload</button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="p-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Review Extracted Questions</h1>
          <div className="space-x-2">
            <button onClick={() => { clearReviewData(); navigate('/ocr-upload'); }} className="px-3 py-2 bg-gray-200 rounded">Cancel</button>
            <button onClick={handleSaveToDb} disabled={saving} className="px-3 py-2 bg-green-600 text-white rounded">{saving ? 'Saving...' : 'Save to DB'}</button>
          </div>
        </div>

        {data.extraction_source && (
          <div className="mb-6 rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
            Extraction source: <span className="font-semibold">{data.extraction_source}</span>
          </div>
        )}

        {data.papers.map((p: any, pIdx: number) => (
          <section key={pIdx} className="mb-6 bg-white p-4 rounded shadow-sm">
            <div className="flex justify-between items-center mb-3">
              <h2 className="font-semibold">Paper {p.paper_number || pIdx+1} {p.paper_name ? `- ${p.paper_name}` : ''}</h2>
              <button onClick={() => addQuestion(pIdx)} className="px-2 py-1 bg-blue-600 text-white rounded text-sm">Add question</button>
            </div>
            <div className="space-y-4">
              {p.questions.map((q: any, qIdx: number) => {
                const originalText = (q.original_question_text || q.question_text || '').trim();
                const suggestedText = (q.grammar_suggestion || '').trim();
                const hasGrammarSuggestion = !!suggestedText && suggestedText !== (q.question_text || '').trim();
                const applyCorrectedText = () => {
                  if (!suggestedText) return;
                  updateQuestionField(pIdx, qIdx, 'question_text', suggestedText);
                };

                return (
                  <div key={qIdx} className="border rounded p-3">
                    <div className="flex justify-between items-center mb-2">
                      <div>Q{q.question_number || qIdx+1}</div>
                      <button className="text-red-600 text-sm" onClick={() => deleteQuestion(pIdx, qIdx)}>Delete</button>
                    </div>
                    <textarea
                      className="w-full border rounded p-2 mb-2"
                      rows={4}
                      value={q.question_text || ''}
                      onChange={(e) => updateQuestionField(pIdx, qIdx, 'question_text', e.target.value)}
                      aria-label={`Question text ${q.question_number || qIdx + 1}`}
                    />

                    {hasGrammarSuggestion && (
                      <div className="mt-2 rounded border border-amber-200 bg-amber-50 p-2 text-sm">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="font-semibold text-amber-800">Grammar & spelling correction</div>
                          <button
                            type="button"
                            onClick={applyCorrectedText}
                            className="px-2 py-1 bg-amber-600 text-white rounded text-xs font-medium"
                          >
                            Use corrected text
                          </button>
                        </div>
                        <div className="text-gray-600 line-through">{originalText || 'No original text captured'}</div>
                        <div className="mt-1 text-amber-900">â†’ {suggestedText}</div>
                      </div>
                    )}

                    <div className="flex items-center gap-4 mt-3">
                      <label className="flex items-center gap-2">Marks <input type="number" className="w-20 p-1 border rounded" value={q.marks || 0} onChange={(e) => updateQuestionField(pIdx, qIdx, 'marks', parseInt(e.target.value || '0'))} /></label>
                      <label className="flex items-center gap-2">
                        CO
                        <input
                          type="text"
                          className="w-20 p-1 border rounded"
                          value={q.course_outcome || ''}
                          placeholder="CO1"
                          onChange={(e) => updateQuestionField(pIdx, qIdx, 'course_outcome', e.target.value)}
                          aria-label={`Course outcome for question ${q.question_number || qIdx + 1}`}
                        />
                      </label>
                      <label className="flex items-center gap-2"><input type="checkbox" checked={!!q.has_math} onChange={(e) => updateQuestionField(pIdx, qIdx, 'has_math', e.target.checked)} /> Has Math</label>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
};

export default ReviewExtracted;
