import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BadgeCheck,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  MessageSquareDiff,
  ShieldCheck,
  XCircle
} from 'lucide-react';
import SectionHeader from './SectionHeader';
import ComparisonPanel from '../moderator-dashboard/ComparisonPanel';
import ChecklistPanel from '../moderator-dashboard/ChecklistPanel';
import DifficultyPanel from '../moderator-dashboard/DifficultyPanel';
import FairnessPanel from '../moderator-dashboard/FairnessPanel';
import InlineCommentsPanel, { InlineIssue } from '../moderator-dashboard/InlineCommentsPanel';
import DecisionSummaryPanel from '../moderator-dashboard/DecisionSummaryPanel';

type AssignedPaper = {
  id: string;
  title: string;
  code: string;
  branch: string;
  semester: string;
  status: 'Awaiting Review' | 'Needs Corrections' | 'Approved' | 'Rejected';
  due: string;
  subject: string;
  reviewer: string;
  draftQuestions: string[];
  changeLog?: Array<{ id: string; timestamp: string; by: string; action: string; details: any }>;
  issues: InlineIssue[];
};

type FinalizedPaper = {
  course: string;
  semester: string;
  subject: string;
  code: string;
  reviewer: string;
  feedback: string;
  approvedAt: string;
};

const assignedPapersSeed: AssignedPaper[] = [
  {
    id: 'dbms-6',
    title: 'DBMS Midterm',
    code: 'DBMS-601',
    branch: 'CSE',
    semester: '6',
    status: 'Awaiting Review',
    due: 'Today, 6:00 PM',
    subject: 'Database Management Systems',
    reviewer: 'Exam Cell',
    draftQuestions: [
      'Q1. Explain normalization and its forms with examples.',
      'Q2. Compare clustered and non-clustered indexes.',
      'Q3. Design an ER diagram for a hospital management system.'
    ],
    issues: [
      {
        id: 'dbms-1',
        label: 'Q1.',
        marks: '10 Marks',
        level: 'Analyze',
        text: 'Explain normalization and its forms',
        highlight: 'with examples.',
        comment: ''
      }
    ]
  },
  {
    id: 'os-5',
    title: 'Operating Systems - Unit Test',
    code: 'OS-502',
    branch: 'CSE',
    semester: '5',
    status: 'Needs Corrections',
    due: 'Tomorrow, 10:00 AM',
    subject: 'Operating Systems',
    reviewer: 'Exam Cell',
    draftQuestions: [
      'Q1. Define deadlock and list conditions.',
      'Q2. Differentiate paging and segmentation.',
      'Q3. Explain CPU scheduling algorithms.'
    ],
    issues: [
      {
        id: 'os-1',
        label: 'Q2.',
        marks: '8 Marks',
        level: 'Understand',
        text: 'Differentiate paging and segmentation',
        highlight: 'with a memory map.',
        comment: ''
      }
    ]
  },
  {
    id: 'se-6',
    title: 'Software Engineering - QQP-2026',
    code: 'SE-601',
    branch: 'CSE',
    semester: '6',
    status: 'Awaiting Review',
    due: 'Today, 8:00 PM',
    subject: 'Software Engineering',
    reviewer: 'Exam Cell',
    draftQuestions: [
      'Q1. Explain software process models.',
      'Q2. Compare Agile and Waterfall methods.',
      'Q3. Write short notes on testing strategies.'
    ],
    issues: [
      {
        id: 'se-1',
        label: 'Q1.',
        marks: '10 Marks',
        level: 'Remember',
        text: 'Explain software process models',
        highlight: 'and contrast with iterative models.',
        comment: ''
      }
    ]
  }
];

const storageKey = 'eduquest-finalized-papers';

function readFinalizedPapers(): FinalizedPaper[] {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveFinalizedPaper(paper: FinalizedPaper) {
  const existing = readFinalizedPapers();
  const next = [
    ...existing.filter((entry) => entry.code !== paper.code),
    paper
  ];
  localStorage.setItem(storageKey, JSON.stringify(next));
}

export default function ModerationSection() {
  const [papers, setPapers] = useState(assignedPapersSeed);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [feedbackByPaper, setFeedbackByPaper] = useState<Record<string, string>>({});
  const [lastAction, setLastAction] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showAllDrafts, setShowAllDrafts] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [editingQuestionIndex, setEditingQuestionIndex] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');

  const selectedPaper = papers[selectedIndex] || (papers.length ? papers[0] : null as any);
  const activeIssues = selectedPaper.issues;
  const selectedFeedback = selectedPaper ? feedbackByPaper[selectedPaper.code] || '' : '';

  const commentCount = useMemo(() => activeIssues.filter((issue) => issue.comment.trim().length > 0).length, [activeIssues]);

  const updateInlineComment = (issueId: string, comment: string) => {
    setPapers((prev) =>
      prev.map((paper) =>
        paper.code === selectedPaper.code
          ? {
              ...paper,
              issues: paper.issues.map((issue) => (issue.id === issueId ? { ...issue, comment } : issue))
            }
          : paper
      )
    );
  };

  const handleFeedbackChange = (value: string) => {
    setFeedbackByPaper((prev) => ({ ...prev, [selectedPaper.code]: value }));
  };

  const handleApprove = () => {
    setPapers((prev) =>
      prev.map((paper) =>
        paper.code === selectedPaper.code ? { ...paper, status: 'Approved' } : paper
      )
    );
    saveFinalizedPaper({
      course: selectedPaper.branch,
      semester: selectedPaper.semester,
      subject: selectedPaper.subject,
      code: selectedPaper.code,
      reviewer: 'Faculty Reviewer',
      feedback: selectedFeedback,
      approvedAt: new Date().toLocaleString()
    });
    // record moderation action
    recordModerationAction(selectedPaper.code, 'approved', { by: 'Reviewer', feedback: selectedFeedback, paper: selectedPaper });
    setLastAction(`${selectedPaper.title} approved and sent to the admin finalized papers store.`);
  };

  const handleReject = () => {
    setPapers((prev) =>
      prev.map((paper) =>
        paper.code === selectedPaper.code ? { ...paper, status: 'Rejected' } : paper
      )
    );
    recordModerationAction(selectedPaper.code, 'rejected', { by: 'Reviewer', feedback: selectedFeedback });
    setLastAction(`${selectedPaper.title} rejected and returned with faculty feedback.`);
  };

  const recordModerationAction = (code: string, action: string, details: any) => {
    try {
      const key = 'eduquest-moderation-records';
      const raw = localStorage.getItem(key);
      const existing = raw ? JSON.parse(raw) : [];
      const entry = {
        id: `${code}-${Date.now()}`,
        code,
        action,
        details,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem(key, JSON.stringify([entry, ...existing]));
      // also append to the paper's changeLog in memory
      setPapers((prev) => prev.map((p) => p.code === code ? { ...p, changeLog: [...(p.changeLog||[]), { id: entry.id, timestamp: entry.timestamp, by: details.by || 'Reviewer', action, details }] } : p));
    } catch (e) {
      console.error('Failed to record moderation action', e);
    }
  };

  const handleSaveQuestionEdit = (index: number) => {
    if (editingText.trim() === '') return;
    const code = selectedPaper.code;
    setPapers((prev) => prev.map((p) => {
      if (p.code !== code) return p;
      const nextQuestions = [...p.draftQuestions];
      const oldText = nextQuestions[index];
      nextQuestions[index] = editingText;
      return { ...p, draftQuestions: nextQuestions, changeLog: [...(p.changeLog||[]), { id: `${code}-${Date.now()}`, timestamp: new Date().toISOString(), by: 'Reviewer', action: 'edit-question', details: { index, oldText, newText: editingText } }] };
    }));
    recordModerationAction(code, 'edit-question', { by: 'Reviewer', index, oldText: selectedPaper.draftQuestions[index], newText: editingText });
    setEditingQuestionIndex(null);
    setEditingText('');
    setLastAction('Question updated and recorded.');
  };

  const handleSaveAndSendToFaculty = () => {
    const code = selectedPaper.code;
    // mark as needs corrections and record
    setPapers((prev) => prev.map((p) => p.code === code ? { ...p, status: 'Needs Corrections' } : p));
    recordModerationAction(code, 'sent-to-faculty', { by: 'Reviewer', feedback: feedbackByPaper[code] || '', paper: selectedPaper });
    setLastAction(`${selectedPaper.title} saved and sent back to faculty for corrections.`);
    setIsFullscreen(false);
  };

  return (
    <section id="moderation" className="px-4 pb-8 md:px-8">
      <SectionHeader
        title="Moderation Queue"
        subtitle="Faculty reviewers see assigned papers here, add feedback, and approve or reject before final storage in the admin dashboard."
        icon={ShieldCheck}
      />

      <div className="grid gap-6">
        {/* Only show list by default */}
        <div className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-xl backdrop-blur-xl">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-600">Assigned Papers</p>
              <h3 className="mt-1 text-xl font-bold text-slate-900">Review list</h3>
            </div>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
              {papers.filter((paper) => paper.status === 'Awaiting Review' || paper.status === 'Needs Corrections').length} pending
            </span>
          </div>

          <div className="mt-5 space-y-3">
            {papers.map((paper, index) => (
              <button
                key={paper.code}
                onClick={() => {
                  setSelectedIndex(index);
                  setIsFullscreen(true);
                }}
                className={`w-full rounded-2xl border p-4 text-left transition ${
                  selectedIndex === index
                    ? 'border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-amber-200 hover:bg-amber-50/40'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-slate-900">{paper.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{paper.code} • {paper.branch} • Sem {paper.semester}</p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wide ${
                    paper.status === 'Approved'
                      ? 'bg-emerald-100 text-emerald-700'
                      : paper.status === 'Rejected'
                      ? 'bg-rose-100 text-rose-700'
                      : paper.status === 'Needs Corrections'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {paper.status}
                  </span>
                </div>
                <p className="mt-3 text-xs text-slate-500 flex items-center gap-1.5">
                  <CalendarDays className="h-3.5 w-3.5" /> Due {paper.due}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Fullscreen modal for selected paper */}
        {isFullscreen && (
          <div className="fixed inset-0 z-50 flex items-start justify-center p-6 bg-black/40">
            <div className="w-full max-w-6xl max-h-[90vh] overflow-auto rounded-3xl bg-white p-6 shadow-2xl">
              <div className="flex items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-2xl font-bold">{selectedPaper.title}</h2>
                  <p className="text-sm text-slate-500">{selectedPaper.code} • {selectedPaper.branch} • Semester {selectedPaper.semester}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => setIsFullscreen(false)} className="text-sm px-3 py-2 rounded-lg border bg-white">Close</button>
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <FileText className="h-4 w-4 text-amber-600" /> Draft Paper Preview
                  </div>
                  <div className="mt-4 space-y-3 text-sm text-slate-700">
                    {selectedPaper.draftQuestions.map((question, qIndex) => (
                      <div key={`${selectedPaper.code}-q-${qIndex}`} className="rounded-xl border border-white bg-white px-4 py-3 shadow-sm flex items-start justify-between gap-3">
                        <div className="flex-1">
                          {editingQuestionIndex === qIndex ? (
                            <div>
                              <textarea
                                className="w-full p-3 rounded-lg border"
                                rows={3}
                                value={editingText}
                                onChange={(e) => setEditingText(e.target.value)}
                              />
                              <div className="mt-2 flex gap-2">
                                <button onClick={() => handleSaveQuestionEdit(qIndex)} className="px-3 py-2 bg-amber-600 text-white rounded-lg text-sm">Save</button>
                                <button onClick={() => { setEditingQuestionIndex(null); setEditingText(''); }} className="px-3 py-2 border rounded-lg text-sm">Cancel</button>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <div className="text-slate-800">{question}</div>
                            </div>
                          )}
                        </div>
                        <div className="flex-shrink-0">
                          {editingQuestionIndex === qIndex ? null : (
                            <button onClick={() => { setEditingQuestionIndex(qIndex); setEditingText(question); }} className="px-3 py-2 rounded-lg border text-sm">Edit</button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
                  <div>
                    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <MessageSquareDiff className="h-4 w-4 text-amber-600" /> Feedback and changes
                      </div>
                      <textarea
                        rows={6}
                        value={feedbackByPaper[selectedPaper.code] || ''}
                        onChange={(e) => handleFeedbackChange(e.target.value)}
                        placeholder="Write the moderation feedback and requested changes here..."
                        className="mt-3 w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 outline-none transition focus:border-amber-300 focus:ring-2 focus:ring-amber-200"
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <ClipboardCheck className="h-4 w-4 text-amber-600" /> Review checklist
                      </div>
                      <ul className="mt-3 space-y-2 text-sm text-slate-600">
                        <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Syllabus coverage checked</li>
                        <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Question difficulty balanced</li>
                        <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Marks align with outcomes</li>
                        <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Feedback recorded for faculty</li>
                      </ul>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                      <div className="flex items-center gap-2 font-semibold text-slate-800">
                        <BookOpen className="h-4 w-4 text-blue-600" /> Moderation ready
                      </div>
                      <p className="mt-2 leading-6">
                        Approved papers are stored in the admin dashboard by course and semester as the finalized paper record.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => { handleSaveAndSendToFaculty(); }}
                    className="inline-flex items-center gap-2 rounded-2xl border border-amber-300 bg-amber-50 px-5 py-3 font-semibold text-amber-700 transition hover:bg-amber-100"
                  >
                    Send to Faculty
                  </button>
                  <button
                    type="button"
                    onClick={() => { handleReject(); setIsFullscreen(false); }}
                    className="inline-flex items-center gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-3 font-semibold text-rose-700 transition hover:bg-rose-100"
                  >
                    <XCircle className="h-4 w-4" /> Reject
                  </button>
                  <button
                    type="button"
                    onClick={() => { handleApprove(); setIsFullscreen(false); }}
                    className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-3 font-semibold text-white shadow-lg shadow-emerald-500/20 transition hover:from-emerald-700 hover:to-teal-700"
                  >
                    <BadgeCheck className="h-4 w-4" /> Approve and Finalize
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}