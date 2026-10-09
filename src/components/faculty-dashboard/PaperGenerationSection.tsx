import { useEffect, useMemo, useState } from 'react';
import { Download, FileCheck2, Loader2, Plus, Wand2, X } from 'lucide-react';
import SectionHeader from './SectionHeader';
import { API_CONFIG, BRANCHES, SEMESTERS } from '../../utils/constants';

type RUA = { R: number; U: number; A: number };
type Pattern = { generate: number; attempt: number; marks: number };
type SubjectOption = {
  subject_id: number | string;
  subject_name: string;
  subject_code: string;
  branch: string;
  semester: number | string;
};

function isSubjectOption(value: unknown): value is SubjectOption {
  if (!value || typeof value !== 'object') return false;
  const subject = value as Record<string, unknown>;
  return (
    (typeof subject.subject_id === 'number' || typeof subject.subject_id === 'string') &&
    typeof subject.subject_name === 'string' &&
    typeof subject.subject_code === 'string' &&
    typeof subject.branch === 'string' &&
    (typeof subject.semester === 'number' || typeof subject.semester === 'string')
  );
}

type GeneratedQuestion = {
  canonical_id: string;
  question_text: string;
  unit: string;
  marks: number;
  rua: string | Record<string, number>;
  difficulty: string;
  course_outcome: string;
};
type GeneratedPaperReview = {
  paper_information: {
    subject: string;
    subject_code: string;
    branch: string;
    semester: number | string;
    exam_type: string;
    paper_total_marks: number;
  };
  sections: Record<string, {
    questions_to_attempt: number;
    questions: GeneratedQuestion[];
  }>;
};

const unitNames = ['Unit-I', 'Unit-II', 'Unit-III', 'Unit-IV', 'Unit-V'];

export default function PaperGenerationSection() {
  const [branch, setBranch] = useState(BRANCHES[0]);
  const [semester, setSemester] = useState('4');
  const [databaseSubjects, setDatabaseSubjects] = useState<SubjectOption[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [subjectLoadError, setSubjectLoadError] = useState<string | null>(null);
  const [examType, setExamType] = useState('University');
  const [totalMarks, setTotalMarks] = useState(70);
  const [selectedUnits, setSelectedUnits] = useState(unitNames);
  const [difficulty, setDifficulty] = useState({ Easy: 40, Medium: 26, Hard: 28 });
  const [rua, setRua] = useState<Record<string, RUA>>(
    Object.fromEntries([
      ['Unit-I', { R: 2, U: 6, A: 6 }],
      ['Unit-II', { R: 6, U: 8, A: 8 }],
      ['Unit-III', { R: 6, U: 8, A: 8 }],
      ['Unit-IV', { R: 4, U: 6, A: 8 }],
      ['Unit-V', { R: 4, U: 6, A: 8 }],
    ])
  );
  const [cos, setCos] = useState(['CO1']);
  const [newCo, setNewCo] = useState('');
  const [patterns, setPatterns] = useState<Record<string, Pattern>>({
    Q1: { generate: 7, attempt: 5, marks: 2 },
    Q2: { generate: 4, attempt: 3, marks: 4 },
    Q3: { generate: 4, attempt: 3, marks: 4 },
    Q4: { generate: 4, attempt: 3, marks: 4 },
    Q5: { generate: 4, attempt: 3, marks: 4 },
    Q6: { generate: 4, attempt: 3, marks: 4 },
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewPaper, setReviewPaper] = useState<GeneratedPaperReview | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const token = sessionStorage.getItem('authToken') || sessionStorage.getItem('adminToken');

    const loadSubjects = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/paper-generation/subjects`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: controller.signal,
        });
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.error || `Unable to load subjects (HTTP ${response.status}).`);
        }
        if (!Array.isArray(result.subjects) || !result.subjects.every(isSubjectOption)) {
          throw new Error('The subject list response is missing required subject metadata.');
        }
        setDatabaseSubjects(result.subjects);
      } catch (loadError) {
        if (!controller.signal.aborted) {
          setSubjectLoadError(
            loadError instanceof Error ? loadError.message : 'Unable to load subjects.'
          );
        }
      }
    };

    void loadSubjects();
    return () => controller.abort();
  }, []);

  const availableSubjects = useMemo(
    () => databaseSubjects.filter((option) =>
      option.branch === branch &&
      String(option.semester) === semester &&
      option.subject_code.trim() !== ''
    ),
    [branch, databaseSubjects, semester]
  );
  const selectedSubject = availableSubjects.find(
    (option) => String(option.subject_id) === selectedSubjectId
  );

  useEffect(() => {
    if (selectedSubject) return;
    setSelectedSubjectId(String(availableSubjects[0]?.subject_id ?? ''));
  }, [availableSubjects, selectedSubject]);

  const ruaTotal = useMemo(
    () => selectedUnits.reduce((sum, unit) => sum + Object.values(rua[unit]).reduce((a, b) => a + b, 0), 0),
    [rua, selectedUnits]
  );
  const difficultyTotal = difficulty.Easy + difficulty.Medium + difficulty.Hard;
  const generatedTotal = Object.values(patterns).reduce((sum, item) => sum + item.generate * item.marks, 0);
  const attemptedTotal = Object.values(patterns).reduce((sum, item) => sum + item.attempt * item.marks, 0);
  const ruaAllocation = selectedUnits.reduce<Record<string, RUA & { Total: number }>>((allocation, unit) => {
    const values = rua[unit] || { R: 0, U: 0, A: 0 };
    allocation[unit] = {
      ...values,
      Total: values.R + values.U + values.A,
    };
    return allocation;
  }, {});

  const updateBranch = (value: string) => {
    setBranch(value);
    setSelectedSubjectId('');
  };

  const updateSemester = (value: string) => {
    setSemester(value);
    setSelectedSubjectId('');
  };

  const updateRua = (unit: string, key: keyof RUA, value: number) => {
    setRua((current) => ({ ...current, [unit]: { ...current[unit], [key]: Math.max(0, value) } }));
  };

  const updatePattern = (section: string, key: keyof Pattern, value: number) => {
    setPatterns((current) => ({ ...current, [section]: { ...current[section], [key]: Math.max(1, value) } }));
  };

  const addPattern = () => {
    const next = Object.keys(patterns).length + 1;
    setPatterns((current) => ({ ...current, [`Q${next}`]: { generate: 1, attempt: 1, marks: 1 } }));
  };

  const addCo = () => {
    const value = newCo.trim().toUpperCase();
    if (value && !cos.includes(value)) setCos((current) => [...current, value]);
    setNewCo('');
  };

  const generatePaper = async () => {
    setError(null);
    setReviewPaper(null);
    if (!selectedSubject || !selectedUnits.length || difficultyTotal !== generatedTotal || ruaTotal !== generatedTotal || attemptedTotal !== totalMarks) {
      setError(`Check the form: generated pool ${generatedTotal}, difficulty ${difficultyTotal}/${generatedTotal}, R/U/A ${ruaTotal}/${generatedTotal}, attempted marks ${attemptedTotal}/${totalMarks}.`);
      return;
    }
    const token = sessionStorage.getItem('authToken') || sessionStorage.getItem('adminToken');
    if (!token) {
      setError('Faculty or admin authorization is required to generate a paper.');
      return;
    }

    const payload = {
      branch: selectedSubject.branch,
      semester: Number(selectedSubject.semester),
      subject: selectedSubject.subject_name,
      subject_id: selectedSubject.subject_id,
      subject_code: selectedSubject.subject_code,
      exam_type: examType,
      total_marks: totalMarks,
      selected_units: selectedUnits,
      difficulty_allocation: difficulty,
      rua_allocation: ruaAllocation,
      co_requirements: cos,
      question_pattern: Object.fromEntries(Object.entries(patterns).map(([name, item]) => [name, {
        questions_to_generate: item.generate,
        questions_to_attempt: item.attempt,
        marks_per_question: item.marks,
      }])),
      instructions: [],
    };

    setBusy(true);
    try {
      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/generate-question-paper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        const pipeline = result.pipeline || {};
        const details = pipeline.errors?.join(', ') || pipeline.error;
        throw new Error(
          result.message
            ? `${pipeline.stage ? `${pipeline.stage}: ` : ''}${result.message}`
            : details
            ? `${pipeline.stage ? `${pipeline.stage}: ` : ''}${details}`
            : result.error || `HTTP ${response.status}`
        );
      }
      const generated = await response.json() as GeneratedPaperReview;
      if (!generated.sections || !generated.paper_information) {
        throw new Error('The generated paper could not be prepared for review.');
      }
      setReviewPaper(generated);
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : 'Paper generation failed.');
    } finally {
      setBusy(false);
    }
  };

  const updateReviewedQuestion = (sectionName: string, questionIndex: number, text: string) => {
    setReviewPaper((current) => {
      if (!current) return current;
      const section = current.sections[sectionName];
      return {
        ...current,
        sections: {
          ...current.sections,
          [sectionName]: {
            ...section,
            questions: section.questions.map((question, index) =>
              index === questionIndex ? { ...question, question_text: text } : question
            ),
          },
        },
      };
    });
  };

  const downloadReviewedPaper = async () => {
    if (!reviewPaper) return;
    setError(null);
    setBusy(true);
    try {
      const token = sessionStorage.getItem('authToken') || sessionStorage.getItem('adminToken');
      if (!token) throw new Error('Faculty or admin authorization is required to download this paper.');
      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/download-reviewed-paper`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(reviewPaper),
      });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        throw new Error(result.error || `Unable to create the reviewed DOCX (HTTP ${response.status}).`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const safeSubject = reviewPaper.paper_information.subject.replace(/[^A-Za-z0-9_-]+/g, '_');
      link.href = url;
      link.download = `${safeSubject || 'EduQuest'}_Question_Paper.docx`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : 'Unable to download the reviewed paper.');
    } finally {
      setBusy(false);
    }
  };

  if (reviewPaper) {
    const paperInformation = reviewPaper.paper_information;
    const sections = Object.entries(reviewPaper.sections);
    const questionCount = sections.reduce((total, [, section]) => total + section.questions.length, 0);

    return (
      <section className="px-4 py-8 md:px-8">
        <SectionHeader title="Review Generated Paper" subtitle="Check the generated questions before approving and downloading the DOCX." icon={FileCheck2} />
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl">
            <div>
              <h2 className="text-xl font-bold text-slate-800">{paperInformation.subject}</h2>
              <p className="mt-1 text-sm text-slate-600">
                {paperInformation.branch} · Semester {paperInformation.semester} · {paperInformation.exam_type}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                {questionCount} questions · {paperInformation.paper_total_marks} marks
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button type="button" onClick={() => setReviewPaper(null)} className="rounded-xl border border-slate-300 px-4 py-2.5 font-semibold text-slate-700 hover:bg-slate-50">
                Revise configuration
              </button>
              <button type="button" onClick={downloadReviewedPaper} disabled={busy} className="rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 px-4 py-2.5 font-semibold text-white shadow-md disabled:cursor-wait disabled:opacity-60">
                {busy ? <Loader2 className="mr-2 inline h-4 w-4 animate-spin" /> : <Download className="mr-2 inline h-4 w-4" />}
                {busy ? 'Preparing DOCX...' : 'Approve and download'}
              </button>
            </div>
          </div>

          {sections.map(([sectionName, section]) => (
            <section key={sectionName} className="rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl">
              <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-lg font-bold text-slate-800">{sectionName}</h3>
                <p className="text-sm text-slate-600">
                  {section.questions.length} generated · attempt {section.questions_to_attempt}
                </p>
              </div>
              <ol className="space-y-3">
                {section.questions.map((question, index) => (
                  <li key={question.canonical_id} className="rounded-xl border border-slate-200 bg-white p-4">
                    <div className="flex items-start justify-between gap-4">
                      <label className="flex-1 text-sm font-semibold text-slate-600">
                        Question {index + 1}
                        <textarea
                          value={question.question_text}
                          onChange={(event) => updateReviewedQuestion(sectionName, index, event.target.value)}
                          rows={3}
                          required
                          aria-label={`Edit ${sectionName} question ${index + 1}`}
                          className="mt-2 w-full resize-y rounded-lg border border-slate-300 bg-white p-3 font-medium text-slate-800 focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500/20"
                        />
                      </label>
                      <span className="shrink-0 rounded-full bg-orange-50 px-3 py-1 text-sm font-semibold text-orange-800">
                        {question.marks} marks
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1">{question.unit}</span>
                      <span className="rounded-full bg-slate-100 px-2.5 py-1">{question.difficulty}</span>
                      {question.course_outcome && <span className="rounded-full bg-slate-100 px-2.5 py-1">{question.course_outcome}</span>}
                    </div>
                  </li>
                ))}
              </ol>
            </section>
          ))}
          {error && <p role="alert" className="text-sm font-medium text-red-700">{error}</p>}
        </div>
      </section>
    );
  }

  return (
    <section className="px-4 py-8 md:px-8">
      <SectionHeader title="Paper Generation" subtitle="Configure the paper requirements and generate a validated DOCX question paper." icon={FileCheck2} />
      <div className="space-y-6">
        <div className="grid gap-4 rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl backdrop-blur-xl md:grid-cols-2 lg:grid-cols-4">
          <label className="text-sm font-semibold text-slate-700">Branch<select value={branch} onChange={(e) => updateBranch(e.target.value)} className="form-select">{BRANCHES.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label className="text-sm font-semibold text-slate-700">Semester<select value={semester} onChange={(e) => updateSemester(e.target.value)} className="form-select">{SEMESTERS.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label className="text-sm font-semibold text-slate-700">Subject<select aria-label="Subject" value={selectedSubjectId} onChange={(e) => setSelectedSubjectId(e.target.value)} disabled={availableSubjects.length === 0} className="form-select"><option value="">Select a registered subject</option>{availableSubjects.map((item) => <option key={item.subject_id} value={String(item.subject_id)}>{item.subject_name} ({item.subject_code})</option>)}</select></label>
          <label className="text-sm font-semibold text-slate-700">Exam type<select value={examType} onChange={(e) => setExamType(e.target.value)} className="form-select"><option>University</option><option>Internal</option><option>Unit Test</option></select></label>
          <label className="text-sm font-semibold text-slate-700">Total marks<input type="number" min="1" value={totalMarks} onChange={(e) => setTotalMarks(Number(e.target.value))} className="form-input" /></label>
        </div>
        {subjectLoadError && <p role="alert" className="text-sm font-medium text-red-700">{subjectLoadError}</p>}
        {!subjectLoadError && availableSubjects.length === 0 && <p role="status" className="text-sm text-slate-600">No registered subjects with subject codes are available for this branch and semester.</p>}

        <div className="grid gap-6 xl:grid-cols-2">
          <div className="rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl">
            <h3 className="text-lg font-semibold">Units and difficulty</h3>
            <div className="mt-4 flex flex-wrap gap-2">{unitNames.map((unit) => <button type="button" key={unit} onClick={() => setSelectedUnits((current) => current.includes(unit) ? current.filter((item) => item !== unit) : [...current, unit])} className={`rounded-xl px-4 py-2 text-sm font-semibold ${selectedUnits.includes(unit) ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-500'}`}>{unit}</button>)}</div>
            <div className="mt-6 grid grid-cols-3 gap-3">{Object.entries(difficulty).map(([key, value]) => <label key={key} className="text-sm font-semibold text-slate-700">{key}<input type="number" min="0" value={value} onChange={(e) => setDifficulty((current) => ({ ...current, [key]: Number(e.target.value) }))} className="form-input" /></label>)}</div>
            <p className={`mt-3 text-sm ${difficultyTotal === generatedTotal ? 'text-emerald-700' : 'text-red-700'}`}>Difficulty total: {difficultyTotal} / generated {generatedTotal}</p>
          </div>
          <div className="rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl">
            <h3 className="text-lg font-semibold">R/U/A marks by unit</h3>
            <div className="mt-4 space-y-3">{selectedUnits.map((unit) => <div key={unit} className="grid grid-cols-4 items-end gap-2"><span className="text-sm font-semibold">{unit}</span>{(['R', 'U', 'A'] as const).map((key) => <label key={key} className="text-xs text-slate-500">{key}<input type="number" min="0" value={rua[unit][key]} onChange={(e) => updateRua(unit, key, Number(e.target.value))} className="form-input" /></label>)}</div>)}</div>
            <p className={`mt-3 text-sm ${ruaTotal === generatedTotal ? 'text-emerald-700' : 'text-red-700'}`}>R/U/A total: {ruaTotal} / generated {generatedTotal}</p>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <div className="rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl">
            <h3 className="text-lg font-semibold">Course outcomes</h3>
            <div className="mt-4 flex flex-wrap gap-2">{cos.map((co) => <span key={co} className="rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-800">{co}<button type="button" onClick={() => setCos((current) => current.filter((item) => item !== co))} className="ml-2"><X className="inline h-3 w-3" /></button></span>)}</div>
            <div className="mt-4 flex gap-2"><input value={newCo} onChange={(e) => setNewCo(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addCo()} placeholder="e.g. CO2" className="form-input" /><button type="button" onClick={addCo} className="rounded-xl bg-slate-800 px-3 text-white"><Plus className="h-4 w-4" /></button></div>
          </div>
          <div className="rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl">
            <div className="flex items-center justify-between"><h3 className="text-lg font-semibold">Question pattern</h3><button type="button" onClick={addPattern} className="text-sm font-semibold text-orange-600"><Plus className="mr-1 inline h-4 w-4" />Add section</button></div>
            <div className="mt-4 space-y-3">{Object.entries(patterns).map(([name, item]) => <div key={name} className="grid grid-cols-4 items-end gap-2"><span className="text-sm font-semibold">{name}</span>{([['generate', 'Generate'], ['attempt', 'Attempt'], ['marks', 'Marks each']] as const).map(([key, label]) => <label key={key} className="text-xs text-slate-500">{label}<input type="number" min="1" value={item[key]} onChange={(e) => updatePattern(name, key, Number(e.target.value))} className="form-input" /></label>)}</div>)}</div>
            <p className={`mt-3 text-sm ${attemptedTotal === totalMarks ? 'text-emerald-700' : 'text-red-700'}`}>Attempted marks: {attemptedTotal} / {totalMarks}</p>
          </div>
        </div>

        <div className="rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl">
          <button type="button" onClick={generatePaper} disabled={busy} className="rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 px-5 py-3 font-semibold text-white shadow-md disabled:opacity-60">{busy ? <Loader2 className="mr-2 inline h-4 w-4 animate-spin" /> : <Wand2 className="mr-2 inline h-4 w-4" />}{busy ? 'Running integrated pipeline...' : 'Generate question paper'}</button>
          {error && <p className="mt-3 text-sm font-medium text-red-700">{error}</p>}
        </div>
      </div>
      <style>{`.form-input,.form-select{margin-top:.35rem;width:100%;border-radius:.75rem;border:1px solid #cbd5e1;background:white;padding:.6rem .75rem;font-size:.875rem;font-weight:400}.form-input:focus,.form-select:focus{outline:2px solid #fbbf24}`}</style>
    </section>
  );
}
