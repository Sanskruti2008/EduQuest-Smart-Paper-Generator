import React, { useState } from 'react';
import { ArrowLeft, Upload, CheckCircle, XCircle, BookOpen, Layers, FileText, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { API_CONFIG } from '../utils/constants';

// ── Types ────────────────────────────────────────────────────────────────────

interface Unit {
  unit_number: number;
  unit_name: string;
  hours?: number;
  course_outcome: string;
  topics: { topic_name: string; subtopics: string[] }[];
}

interface CurriculumResult {
  success: boolean;
  subject_name?: string;
  subject_code?: string;
  total_units?: number;
  filename?: string;
  db_result?: { units_saved: number; topics_saved: number; subtopics_in_json: number } | null;
  db_error?: string | null;
  curriculum?: {
    branch?: string;
    semester?: number;
    total_credits?: number;
    total_hours?: number;
    units: Unit[];
    course_outcomes: { co_number: string; description: string }[];
  };
  error?: string;
}

// ── Branch / subject config (reused from QuestionPaperUpload) ─────────────────

const SEM1_COMMON = [
  'Communication Skills (CMS)',
  'Applied Mathematics',
  'Applied Science',
  'Workshop Technology',
  'Engineering Drawing',
];

const BRANCH_CONFIG: Record<string, { semesters: string[]; subjects: Record<string, string[]> }> = {
  'Computer Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Basic Electronics', 'Digital Techniques', 'Programming in C', 'Applied Mathematics – II', 'Engineering Graphics'],
      '3': ['Data Structures using C', 'Digital Electronics', 'Computer Organization', 'Object Oriented Programming', 'Discrete Mathematics'],
      '4': ['Operating Systems', 'Database Management Systems', 'Computer Networks', 'Web Development', 'Software Engineering'],
      '5': ['Microprocessors & Interfaces', 'Advanced Java', 'Artificial Intelligence', 'Information Security', 'Industrial Organization and Management (IOM)', 'Elective – I'],
      '6': ['Mobile Application Development', 'Cloud Computing', 'Machine Learning', 'Project Work', 'Elective – II'],
    },
  },
  'Mechanical Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Applied Mathematics – II', 'Applied Mechanics', 'Material Science', 'Engineering Drawing – II', 'Basic Electronics'],
      '3': ['Engineering Mechanics', 'Strength of Materials', 'Thermodynamics', 'Manufacturing Processes – I', 'Metrology'],
      '4': ['Fluid Mechanics', 'Heat Transfer', 'Manufacturing Processes – II', 'Theory of Machines', 'Industrial Management'],
      '5': ['Machine Design', 'Refrigeration & Air Conditioning', 'CNC Technology', 'Power Plant Engineering', 'Elective – I'],
      '6': ['Mechatronics', 'Automobile Engineering', 'Project Work', 'Industrial Training', 'Elective – II'],
    },
  },
  'Civil Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Applied Mathematics – II', 'Applied Mechanics', 'Building Materials & Construction', 'Engineering Drawing – II', 'Basic Electronics'],
      '3': ['Surveying – I', 'Structural Mechanics', 'Concrete Technology', 'Hydraulics', 'Building Planning & Drawing'],
      '4': ['Surveying – II', 'Structural Analysis', 'Geotechnical Engineering', 'Irrigation Engineering', 'Environmental Engineering'],
      '5': ['Estimation & Costing', 'Reinforced Concrete Structures', 'Highway Engineering', 'Construction Management', 'Elective – I'],
      '6': ['Transportation Engineering', 'Advanced Construction Techniques', 'Computer Aided Design', 'Project Work', 'Elective – II'],
    },
  },
  'Electrical Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Applied Mathematics – II', 'Applied Science – II', 'Basic Electronics', 'Engineering Drawing', 'DC Circuits'],
      '3': ['Circuit Theory', 'Electrical Measurements', 'Digital Electronics', 'AC Circuits', 'Electronic Devices'],
      '4': ['Electrical Machines – I', 'Control Systems', 'Microprocessors', 'Power Electronics', 'Industrial Electronics'],
      '5': ['Electrical Machines – II', 'Power Systems – I', 'Programmable Logic Controllers', 'Electrical Estimation', 'Elective – I'],
      '6': ['Power Systems – II', 'Switchgear & Protection', 'Energy Management', 'Project Work', 'Elective – II'],
    },
  },
};

// ── Component ─────────────────────────────────────────────────────────────────

const CurriculumUpload: React.FC = () => {
  const [file, setFile]         = useState<File | null>(null);
  const [branch, setBranch]     = useState('');
  const [semester, setSemester] = useState('');
  const [subject, setSubject]   = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult]     = useState<CurriculumResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [expandedUnit, setExpandedUnit]   = useState<number | null>(null);
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  const ACCEPTED = '.pdf,.docx,.txt';
  const availableSemesters = branch ? BRANCH_CONFIG[branch]?.semesters ?? [] : [];
  const availableSubjects: string[] =
    branch && semester ? BRANCH_CONFIG[branch]?.subjects[semester] ?? [] : [];

  // ── Drag-and-drop ──────────────────────────────────────────────────────────
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  };
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  // ── Upload ─────────────────────────────────────────────────────────────────
  const handleUpload = async () => {
    if (!file) return alert('Please select a syllabus file.');

    const adminToken = sessionStorage.getItem('adminToken');
    if (!adminToken) {
      setResult({ success: false, error: 'Admin login required to upload curriculum.' });
      return;
    }

    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    if (branch)   formData.append('branch',   branch);
    if (semester) formData.append('semester', semester);
    if (subject)  formData.append('subject',  subject);

    try {
      const res  = await fetch(`${API_CONFIG.BACKEND_URL}/api/upload-syllabus`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${adminToken}` },
        body:   formData,
      });
      const data: CurriculumResult = await res.json();
      setResult(data);
      if (data.success) { setFile(null); setBranch(''); setSemester(''); setSubject(''); }
    } catch {
      setResult({ success: false, error: 'Network error. Please try again.' });
    } finally {
      setUploading(false);
    }
  };

  // ── UI helpers ─────────────────────────────────────────────────────────────
  const fileExt = file?.name.split('.').pop()?.toLowerCase() ?? '';
  const fileIcon = fileExt === 'pdf' ? '📄' : fileExt === 'docx' ? '📝' : '📃';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link
              to="/faculty-dashboard"
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Dashboard
            </Link>
            <h1 className="text-xl font-bold text-gray-900">Upload Curriculum</h1>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero banner */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl p-6 shadow-lg">
          <h2 className="text-2xl font-bold mb-1">📚 Curriculum / Syllabus Extractor</h2>
          <p className="text-indigo-100 text-sm">
            Upload your MSBTE subject syllabus (PDF, DOCX, or TXT). AI will extract units, topics,
            course outcomes, and store them in the database automatically.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Upload form */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5">
            <h3 className="text-lg font-bold text-gray-800">Upload Syllabus File</h3>

            {/* Drop zone */}
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
                dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('curriculum-file-input')?.click()}
            >
              <input
                id="curriculum-file-input"
                type="file"
                accept={ACCEPTED}
                className="hidden"
                onChange={handleFileChange}
              />
              {file ? (
                <div className="space-y-2">
                  <div className="text-5xl">{fileIcon}</div>
                  <p className="font-semibold text-gray-700">{file.name}</p>
                  <p className="text-sm text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  <button
                    className="text-red-500 hover:text-red-600 text-sm font-medium"
                    onClick={e => { e.stopPropagation(); setFile(null); }}
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                  <p className="font-medium text-gray-600">Drop your syllabus here</p>
                  <p className="text-sm text-gray-400">or click to browse</p>
                  <p className="text-xs text-gray-400 mt-1">PDF · DOCX · TXT</p>
                </div>
              )}
            </div>

            {/* Optional metadata selects */}
            <div className="space-y-3">
              <p className="text-sm text-gray-500 font-medium">
                Optional — helps AI recover garbled OCR fields
              </p>
              {/* Branch */}
              <select
                value={branch}
                onChange={e => { setBranch(e.target.value); setSemester(''); setSubject(''); }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select Branch (optional)</option>
                {Object.keys(BRANCH_CONFIG).map(b => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>

              {/* Semester */}
              {branch && (
                <select
                  value={semester}
                  onChange={e => { setSemester(e.target.value); setSubject(''); }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select Semester (optional)</option>
                  {availableSemesters.map(s => (
                    <option key={s} value={s}>Semester {s}</option>
                  ))}
                </select>
              )}

              {/* Subject */}
              {branch && semester && (
                <select
                  value={subject}
                  onChange={e => setSubject(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select Subject (optional)</option>
                  {availableSubjects.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              )}
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className={`w-full py-3 rounded-xl font-bold text-white transition-all ${
                !file || uploading
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-md'
              }`}
            >
              {uploading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Extracting Curriculum…
                </span>
              ) : (
                'Extract & Save Curriculum'
              )}
            </button>
          </div>

          {/* Right: Features / result */}
          <div className="space-y-5">
            {!result ? (
              <div className="grid grid-cols-1 gap-4">
                {[
                  { icon: '🤖', title: 'AI-Powered Parsing', desc: 'Groq LLaMA-70B intelligently extracts units, topics, and course outcomes from any MSBTE syllabus format.' },
                  { icon: '📋', title: 'Multi-Format Support', desc: 'Accepts scanned PDFs (OCR), Word DOCX, and plain text files.' },
                  { icon: '💾', title: 'Auto-Saved to DB', desc: 'Units and topics are upserted into Supabase so the Question Generator can use them instantly.' },
                  { icon: '🔁', title: 'Regex Fallback', desc: 'If AI is unavailable, a smart regex parser handles standard MSBTE chapter/unit structures.' },
                ].map(f => (
                  <div key={f.title} className="bg-white rounded-xl border border-gray-200 p-4 flex gap-4 shadow-sm">
                    <span className="text-3xl">{f.icon}</span>
                    <div>
                      <h4 className="font-semibold text-gray-800 text-sm">{f.title}</h4>
                      <p className="text-gray-500 text-xs mt-0.5">{f.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : result.success ? (
              /* ── Success card ── */
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-xl p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                    <h3 className="font-bold text-green-800 text-lg">Curriculum Extracted!</h3>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-white rounded-lg p-3 border border-green-100">
                      <p className="text-gray-500 text-xs">Subject</p>
                      <p className="font-semibold text-gray-900 truncate">{result.subject_name || '—'}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-100">
                      <p className="text-gray-500 text-xs">Subject Code</p>
                      <p className="font-semibold text-gray-900">{result.subject_code || '—'}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-100">
                      <p className="text-gray-500 text-xs">Units Found</p>
                      <p className="font-semibold text-gray-900">{result.total_units ?? 0}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-100">
                      <p className="text-gray-500 text-xs">DB Status</p>
                      <p className={`font-semibold ${result.db_error ? 'text-orange-600' : 'text-green-700'}`}>
                        {result.db_error ? 'Save failed' : 'Saved ✓'}
                      </p>
                    </div>
                  </div>
                  {result.db_result && !result.db_error && (
                    <p className="text-xs text-green-700 mt-2">
                      {result.db_result.units_saved} new unit(s) &middot;&nbsp;
                      {result.db_result.topics_saved} topic/subtopic rows added
                      {result.db_result.subtopics_in_json > 0 &&
                        ` (${result.db_result.subtopics_in_json} subtopics in JSON)`
                      }
                    </p>
                  )}
                  {result.db_error && (
                    <p className="text-xs text-orange-600 mt-2">Note: {result.db_error}</p>
                  )}
                </div>

                {/* Unit accordion */}
                {(result.curriculum?.units?.length ?? 0) > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
                      <Layers className="w-4 h-4 text-indigo-600" />
                      <h4 className="font-bold text-gray-700 text-sm">Extracted Units</h4>
                    </div>
                    <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
                      {result.curriculum!.units.map((unit, idx) => (
                        <div key={idx}>
                          <button
                            className="w-full text-left px-5 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                            onClick={() => setExpandedUnit(expandedUnit === idx ? null : idx)}
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center">
                                {unit.unit_number}
                              </span>
                              <span className="text-sm font-medium text-gray-800 truncate">{unit.unit_name}</span>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">
                                {unit.course_outcome}
                              </span>
                              <span className="text-xs text-gray-400">
                                {unit.topics?.length ?? 0} topics
                                {(() => {
                                  const subs = unit.topics?.reduce((n, t) => n + (t.subtopics?.length ?? 0), 0) ?? 0;
                                  return subs > 0 ? ` · ${subs} subtopics` : '';
                                })()}
                              </span>
                              <span className="text-gray-400 text-xs">{expandedUnit === idx ? '▲' : '▼'}</span>
                            </div>
                          </button>
                          {expandedUnit === idx && unit.topics?.length > 0 && (
                            <div className="px-5 pb-3 space-y-1.5">
                              {unit.topics.map((t, ti) => {
                                const topicKey = `${idx}-${ti}`;
                                const hasSubtopics = (t.subtopics?.length ?? 0) > 0;
                                return (
                                  <div key={ti} className="rounded-lg border border-gray-200 bg-white overflow-hidden">
                                    <button
                                      className="w-full text-left flex items-center gap-2 px-3 py-2 hover:bg-gray-50 transition-colors"
                                      onClick={() =>
                                        setExpandedTopic(expandedTopic === topicKey ? null : topicKey)
                                      }
                                      disabled={!hasSubtopics}
                                    >
                                      {hasSubtopics ? (
                                        expandedTopic === topicKey
                                          ? <ChevronDown className="w-3.5 h-3.5 text-indigo-500 flex-shrink-0" />
                                          : <ChevronRight className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                                      ) : (
                                        <FileText className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                                      )}
                                      <span className="text-xs font-medium text-gray-700 flex-1">{t.topic_name}</span>
                                      {hasSubtopics && (
                                        <span className="text-xs text-indigo-500 bg-indigo-50 px-1.5 py-0.5 rounded-full flex-shrink-0">
                                          {t.subtopics.length}
                                        </span>
                                      )}
                                    </button>
                                    {expandedTopic === topicKey && hasSubtopics && (
                                      <div className="border-t border-gray-100 px-3 py-2 space-y-1">
                                        {t.subtopics.map((sub, si) => (
                                          <div key={si} className="flex items-start gap-2 text-xs text-gray-600 py-0.5">
                                            <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-indigo-300 mt-1.5"></span>
                                            <span>{sub}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Course outcomes */}
                {(result.curriculum?.course_outcomes?.length ?? 0) > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-purple-600" />
                      <h4 className="font-bold text-gray-700 text-sm">Course Outcomes</h4>
                    </div>
                    <div className="divide-y divide-gray-100 max-h-48 overflow-y-auto">
                      {result.curriculum!.course_outcomes.map((co, ci) => (
                        <div key={ci} className="px-5 py-2.5 flex items-start gap-3">
                          <span className="flex-shrink-0 text-xs font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full mt-0.5">
                            {co.co_number}
                          </span>
                          <span className="text-xs text-gray-700">{co.description}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => { setResult(null); setExpandedUnit(null); }}
                  className="w-full py-2.5 rounded-xl border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-50 transition-colors"
                >
                  Upload Another Syllabus
                </button>
              </div>
            ) : (
              /* ── Error card ── */
              <div className="bg-red-50 border border-red-200 rounded-xl p-5 space-y-2">
                <div className="flex items-center gap-2">
                  <XCircle className="w-6 h-6 text-red-500" />
                  <h3 className="font-bold text-red-700">Extraction Failed</h3>
                </div>
                <p className="text-sm text-red-600">{result.error}</p>
                <button
                  onClick={() => setResult(null)}
                  className="mt-2 text-sm text-red-500 underline hover:text-red-600"
                >
                  Try again
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CurriculumUpload;
