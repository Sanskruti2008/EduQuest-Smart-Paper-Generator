import { motion } from 'framer-motion';
import { Book, Bookmark, CheckCircle2, GraduationCap, Layers, Loader2 } from 'lucide-react';
import { Fragment, useEffect, useState } from 'react';
import Header from '../components/Header';
import { useQuestionBank } from '../context/QuestionBankContext';
import { API_CONFIG, BRANCHES, SEMESTERS, SUBJECT_CATALOG, formatBranchSemester } from '../utils/constants';

interface SubjectOption {
  subject_id: number | string;
  subject_name: string;
  branch: string;
  semester: number | string;
}

interface UniqueQuestion {
  canonical_id: string | number;
  canonical_question: string;
  subject?: string;
  question_type?: string;
  verb?: string;
}

const QuestionBank = () => {
  const { questions, loading, fetchDbQuestions } = useQuestionBank();
  
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  const [selectedSemester, setSelectedSemester] = useState<string | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | string | null>(null);
  const [databaseSubjects, setDatabaseSubjects] = useState<SubjectOption[]>([]);

  // Fetch DB questions whenever branch + semester are both chosen
  useEffect(() => {
    if (selectedBranch && selectedSemester) {
      fetchDbQuestions(selectedBranch, selectedSemester, selectedSubject, selectedSubjectId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBranch, selectedSemester, selectedSubject, selectedSubjectId]);
  
  const [uniqueQuestions, setUniqueQuestions] = useState<UniqueQuestion[]>([]);
  const [uniqueLoading, setUniqueLoading] = useState(true);
  const [uniqueError, setUniqueError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const token = sessionStorage.getItem('authToken') || sessionStorage.getItem('adminToken');

    const loadSubjects = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/paper-generation/subjects`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: controller.signal,
        });
        if (!response.ok) return;
        const payload = await response.json();
        if (Array.isArray(payload.subjects)) {
          setDatabaseSubjects(payload.subjects);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error('[QuestionBank] Failed to load subject metadata:', error);
        }
      }
    };

    void loadSubjects();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedBranch || !selectedSemester || !selectedSubject) {
      setUniqueQuestions([]);
      setUniqueError(null);
      setUniqueLoading(false);
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    const fetchUniqueQuestions = async () => {
      setUniqueLoading(true);
      setUniqueError(null);
      try {
        const params = new URLSearchParams({
          branch: selectedBranch,
          semester: selectedSemester,
        });
        if (selectedSubjectId !== null) {
          params.set('subject_id', String(selectedSubjectId));
        } else {
          params.set('subject', selectedSubject);
        }
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/unique-question-bank?${params}`, {
          signal: controller.signal,
        });
        window.clearTimeout(timeout);
        const payload = await response.json();
        if (!response.ok || !payload.success) {
          throw new Error(payload.error || `HTTP ${response.status}`);
        }
        setUniqueQuestions(Array.isArray(payload.questions) ? payload.questions : []);
      } catch (error) {
        console.error('[QuestionBank] Failed to load unique question bank:', error);
        setUniqueError(error instanceof Error ? error.message : 'Unable to load unique questions');
      } finally {
        setUniqueLoading(false);
      }
    };

    void fetchUniqueQuestions();
    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [selectedBranch, selectedSemester, selectedSubject, selectedSubjectId]);

  // Get unique values
  const selectedGrade = selectedBranch && selectedSemester ? formatBranchSemester(selectedBranch, selectedSemester) : null;
  const subjects = selectedGrade
    ? Array.from(new Set(questions.filter(q => q.grade === selectedGrade).map(q => q.subject)))
    : [];
  const catalogSubjects = selectedBranch && selectedSemester
    ? SUBJECT_CATALOG[selectedBranch]?.[selectedSemester] || []
    : [];
  const databaseSubjectOptions = selectedBranch && selectedSemester
    ? databaseSubjects.filter(subject =>
        subject.branch === selectedBranch && String(subject.semester) === selectedSemester
      )
    : [];
  const availableSubjects = databaseSubjectOptions.length > 0
    ? databaseSubjectOptions.map(subject => subject.subject_name)
    : (subjects.length > 0 ? subjects : catalogSubjects);

  // Show selection interface if not all selections are made
  if (!selectedBranch || !selectedSemester || !selectedSubject) {
    const selectionSteps = [
      { label: 'Select Branch', active: !!selectedBranch },
      { label: 'Select Semester', active: !!selectedSemester },
      { label: 'Select Subject', active: !!selectedSubject }
    ];

    return (
      <div className="min-h-screen bg-[#f6efe5] text-slate-900">
        <Header title="Question Bank" />
        
        <main className="max-w-5xl mx-auto px-4 py-12 md:py-20">
          <div className="text-center mb-16">
            <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-3">Select Your Preferences</h1>
            <p className="text-slate-600 text-lg">Choose branch, semester, and subject to view question papers</p>
          </div>

          <div className="space-y-8">
            <div className="flex items-center justify-center gap-4 flex-wrap mb-8">
              {selectionSteps.map((step, index) => (
                <Fragment key={step.label}>
                  <div
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-full transition-all ${
                      step.active ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-orange-500/20' : 'bg-white/60 border border-white/60 text-slate-500 hover:bg-white'
                    }`}
                  >
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step.active ? 'bg-white text-orange-500' : 'bg-slate-200 text-slate-600'}`}>
                      {step.active ? <CheckCircle2 className="w-4 h-4" /> : index + 1}
                    </span>
                    <span className="font-semibold text-sm">{step.label}</span>
                  </div>
                  {index < selectionSteps.length - 1 && (
                    <div className="w-8 h-1 bg-amber-200/50 rounded-full"></div>
                  )}
                </Fragment>
              ))}
            </div>

            {/* Branch Selection */}
            {!selectedBranch && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/70 backdrop-blur-xl rounded-2xl p-8 border border-white/60 shadow-xl"
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 text-white flex items-center justify-center font-bold shadow-lg shadow-orange-500/20">
                    <GraduationCap className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-800">Select Branch</h3>
                    <p className="text-sm text-slate-500">Choose your engineering discipline</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {BRANCHES.map(branch => (
                    <button
                      key={branch}
                      onClick={() => {
                        setSelectedBranch(branch);
                        setSelectedSemester(null);
                        setSelectedSubject(null);
                        setSelectedSubjectId(null);
                      }}
                      className={`p-5 rounded-2xl border-2 font-bold text-lg transition-all ${
                        selectedBranch === branch
                          ? 'border-amber-400 bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-lg shadow-orange-500/20 scale-[1.02] border-transparent'
                          : 'bg-white/80 border-white/60 hover:border-amber-300 hover:shadow-md hover:bg-white text-slate-700'
                      }`}
                    >
                      {branch}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Semester Selection */}
            {selectedBranch && !selectedSemester && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/70 backdrop-blur-xl rounded-2xl p-8 border border-white/60 shadow-xl"
              >
                <button
                  onClick={() => {
                    setSelectedBranch(null);
                    setSelectedSemester(null);
                    setSelectedSubject(null);
                    setSelectedSubjectId(null);
                  }}
                  className="flex items-center gap-2 text-slate-600 hover:text-amber-600 font-medium mb-6 transition-colors"
                >
                  <span className="w-4 h-4 rounded-full border border-slate-400 flex items-center justify-center text-[10px]">&larr;</span>
                  Change Branch
                </button>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 text-white flex items-center justify-center font-bold shadow-lg shadow-orange-500/20">
                    <Layers className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-800">Select Semester</h3>
                    <p className="text-sm text-slate-500">Branch: <span className="font-semibold text-amber-600">{selectedBranch}</span></p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {SEMESTERS.map(semester => (
                    <button
                      key={semester}
                      onClick={() => {
                        setSelectedSemester(semester);
                        setSelectedSubject(null);
                        setSelectedSubjectId(null);
                      }}
                      className={`p-5 rounded-2xl border-2 font-bold text-lg transition-all ${
                        selectedSemester === semester
                          ? 'border-amber-400 bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-lg shadow-orange-500/20 scale-[1.02] border-transparent'
                          : 'bg-white/80 border-white/60 hover:border-amber-300 hover:shadow-md hover:bg-white text-slate-700'
                      }`}
                    >
                      {semester}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Subject Selection */}
            {selectedBranch && selectedSemester && !selectedSubject && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/70 backdrop-blur-xl rounded-2xl p-8 border border-white/60 shadow-xl"
              >
                <div className="flex flex-wrap items-center gap-4 mb-6">
                  <button
                    onClick={() => {
                      setSelectedSemester(null);
                      setSelectedSubject(null);
                      setSelectedSubjectId(null);
                    }}
                    className="flex items-center gap-2 text-slate-600 hover:text-amber-600 font-medium transition-colors"
                  >
                    <span className="w-4 h-4 rounded-full border border-slate-400 flex items-center justify-center text-[10px]">&larr;</span>
                    Change Semester
                  </button>
                  <button
                    onClick={() => {
                      setSelectedBranch(null);
                      setSelectedSemester(null);
                      setSelectedSubject(null);
                      setSelectedSubjectId(null);
                    }}
                    className="flex items-center gap-2 text-slate-600 hover:text-amber-600 font-medium transition-colors"
                  >
                    <span className="w-4 h-4 rounded-full border border-slate-400 flex items-center justify-center text-[10px]">&larr;</span>
                    Start Over
                  </button>
                </div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 text-white flex items-center justify-center font-bold shadow-lg shadow-orange-500/20">
                    <Book className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-800">Select Subject</h3>
                    <p className="text-sm text-slate-500">{selectedGrade}</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {availableSubjects.map(subject => (
                    <button
                      key={subject}
                      onClick={() => {
                        setSelectedSubject(subject);
                        const databaseSubject = databaseSubjectOptions.find(
                          option => option.subject_name === subject
                        );
                        setSelectedSubjectId(databaseSubject?.subject_id ?? null);
                      }}
                      className={`p-5 rounded-2xl border-2 font-bold text-lg transition-all text-left flex items-center justify-between group ${
                        selectedSubject === subject
                          ? 'border-amber-400 bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-lg shadow-orange-500/20 scale-[1.02] border-transparent'
                          : 'bg-white/80 border-white/60 hover:border-amber-300 hover:shadow-md hover:bg-white text-slate-700'
                      }`}
                    >
                      <span>{subject}</span>
                      {selectedSubject === subject && <CheckCircle2 className="w-5 h-5 text-white/80" />}
                    </button>
                  ))}
                </div>
                {availableSubjects.length === 0 && (
                  <div className="text-center text-slate-500 mt-10 mb-6">
                    {loading
                      ? <p className="flex flex-col items-center justify-center gap-4 text-amber-600 font-medium bg-amber-50/50 p-6 rounded-2xl border border-amber-100/50"><Loader2 className="w-8 h-8 animate-spin" /> Fetching latest subjects for {selectedGrade}...</p>
                      : <div className="bg-white/50 p-8 rounded-2xl border-2 border-dashed border-slate-200">
                          <Book className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                          <p className="font-semibold text-slate-600">No subjects found</p>
                          <p className="text-sm mt-1">There are currently no questions uploaded for {selectedGrade}.</p>
                        </div>}
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f6efe5] text-slate-900">
    <Header title="Question Bank" />

    {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Current Selection Banner */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-2xl p-6 mb-8 shadow-xl">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="text-xs uppercase tracking-wider text-white/80 mb-2 font-semibold">Current Selection</div>
              <div className="font-bold text-xl drop-shadow-sm">
                {selectedGrade} • {selectedSubject}
              </div>
            </div>
            <button
              onClick={() => {
                setSelectedBranch(null);
                setSelectedSemester(null);
                setSelectedSubject(null);
                setSelectedSubjectId(null);
              }}
              className="px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-white font-semibold transition-all border border-white/40"
            >
              Change Selection
            </button>
          </div>
        </div>

        <section className="mb-8 rounded-2xl border border-emerald-200 bg-emerald-50/80 p-6 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <div>
              <div className="flex items-center gap-2">
                <Bookmark className="w-5 h-5 text-emerald-700" />
                <h2 className="text-xl font-bold text-emerald-950">Unique Question Bank</h2>
              </div>
              <p className="mt-1 text-sm text-emerald-800">
                Canonical questions for {selectedSubject}, {selectedGrade}, retained after similarity checking.
              </p>
            </div>
            <span className="rounded-full bg-white px-3 py-1 text-sm font-semibold text-emerald-700">
              {uniqueQuestions.length} unique
            </span>
          </div>

          {uniqueLoading ? (
            <div className="flex items-center gap-2 rounded-xl bg-white/70 p-4 text-sm text-emerald-800">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading canonical questions...
            </div>
          ) : uniqueError ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              Could not load the unique question bank: {uniqueError}
            </div>
          ) : uniqueQuestions.length === 0 ? (
            <div className="rounded-xl border border-dashed border-emerald-300 bg-white/60 p-5 text-sm text-emerald-800">
              No canonical questions exist for this branch, semester, and subject.
            </div>
          ) : (
            <div className="grid gap-3">
              {uniqueQuestions.map((question) => (
                <article key={question.canonical_id} className="rounded-xl bg-white p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium leading-relaxed text-slate-800">{question.canonical_question}</p>
                    <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-800">
                      {question.canonical_id}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                    {question.subject && <span>{question.subject}</span>}
                    {question.question_type && <span>• {question.question_type}</span>}
                    {question.verb && <span>• Verb: {question.verb}</span>}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

      </main>
    </div>
  );
};

export default QuestionBank;
