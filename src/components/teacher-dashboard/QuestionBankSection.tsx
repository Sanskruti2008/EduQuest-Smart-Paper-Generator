import { Filter, LayoutGrid, LayoutList, LibraryBig, Star } from 'lucide-react';
import { useMemo } from 'react';
import SectionHeader from './SectionHeader';

const questionBank = [
  {
    id: 'Q1',
    subject: 'DBMS',
    unit: 'Unit 2',
    difficulty: 'Medium',
    marks: 10,
    type: 'Descriptive',
    question: 'Explain normalization up to 3NF with examples.'
  },
  {
    id: 'Q2',
    subject: 'OS',
    unit: 'Unit 3',
    difficulty: 'Hard',
    marks: 15,
    type: 'Case Study',
    question: 'Analyze deadlock handling with a real-world scenario.'
  },
  {
    id: 'Q3',
    subject: 'SE',
    unit: 'Unit 1',
    difficulty: 'Easy',
    marks: 5,
    type: 'MCQ',
    question: 'Which SDLC model fits iterative releases?'
  }
];

interface QuestionBankSectionProps {
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;
}

export default function QuestionBankSection({ viewMode, onViewModeChange }: QuestionBankSectionProps) {
  const filteredQuestions = useMemo(() => questionBank, []);

  return (
    <section id="question-bank" className="px-4 pb-8 md:px-8">
      <SectionHeader
        title="Question Bank"
        subtitle="Search, filter, and favorite curated questions with metadata."
        icon={LibraryBig}
      />
      <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <h3 className="text-lg font-semibold">Question Bank</h3>
          <div className="flex items-center gap-3">
            <button
              onClick={() => onViewModeChange('grid')}
              className={`rounded-2xl px-3 py-2 text-xs font-semibold shadow-sm border border-white/60 ${viewMode === 'grid' ? 'bg-amber-100 text-amber-700' : 'bg-white text-slate-600'}`}
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => onViewModeChange('list')}
              className={`rounded-2xl px-3 py-2 text-xs font-semibold shadow-sm border border-white/60 ${viewMode === 'list' ? 'bg-amber-100 text-amber-700' : 'bg-white text-slate-600'}`}
            >
              <LayoutList className="h-4 w-4" />
            </button>
            <button className="rounded-2xl bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm border border-white/60">
              <Filter className="h-4 w-4" /> Filters
            </button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2 text-xs">
          {['Subject', 'Unit', 'Difficulty', 'Marks', 'Question Type'].map((filter) => (
            <span key={filter} className="rounded-full bg-white/80 px-3 py-1 text-slate-600 border border-amber-200">
              {filter}
            </span>
          ))}
        </div>

        <div className={`mt-6 grid gap-4 ${viewMode === 'grid' ? 'md:grid-cols-2' : ''}`}>
          {filteredQuestions.map((question) => (
            <div key={question.id} className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">{question.question}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                    <span className="rounded-full bg-amber-100 px-2 py-1 text-amber-700">{question.subject}</span>
                    <span className="rounded-full bg-orange-100 px-2 py-1 text-orange-700">{question.unit}</span>
                    <span className="rounded-full bg-white px-2 py-1 border border-amber-200 text-slate-600">{question.difficulty}</span>
                    <span className="rounded-full bg-white px-2 py-1 border border-amber-200 text-slate-600">{question.marks} Marks</span>
                    <span className="rounded-full bg-white px-2 py-1 border border-amber-200 text-slate-600">{question.type}</span>
                  </div>
                </div>
                <button className="rounded-full bg-white p-2 shadow-sm border border-white/60">
                  <Star className="h-4 w-4 text-amber-400" />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div key={item} className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm animate-pulse">
              <div className="h-4 w-3/4 rounded bg-slate-200"></div>
              <div className="mt-3 h-3 w-1/2 rounded bg-slate-200"></div>
              <div className="mt-3 h-3 w-2/3 rounded bg-slate-200"></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
