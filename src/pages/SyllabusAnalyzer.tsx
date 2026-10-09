import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { API_CONFIG } from '../utils/constants';
import { 
  ArrowLeft, BookOpen, CheckCircle, AlertCircle, XCircle, 
  TrendingUp, Award, Target, FileText, ChevronDown, ChevronRight,
  Book, Brain, Lightbulb, Clock, BarChart3
} from 'lucide-react';

interface RUAMapping {
  depth: string;
  concepts: string[];
  exam_priority: string;
  typical_marks: string;
  question_types: string[];
}

interface Topic {
  topic_id: string;
  topic_name: string;
  subtopics: string[];
  rua_mapping: {
    remember?: RUAMapping;
    understand?: RUAMapping;
    apply?: RUAMapping;
  };
  focus_type: string;
}

interface RUASummary {
  remember_coverage: string;
  understand_coverage: string;
  apply_coverage: string;
  overall_compliance: string;
  recommendations: string[];
}

interface Chapter {
  chapter_number: number;
  chapter_name: string;
  chapter_code: string;
  hours_allocated: number;
  weightage_percentage: number;
  learning_objectives: string[];
  topics: Topic[];
  rua_summary: RUASummary;
}

interface Subject {
  subject_id: string;
  subject_name: string;
  branch: string;
  semester: number;
  total_credits: number;
  total_hours: number;
  chapters: Chapter[];
  overall_rua_analysis?: {
    remember_distribution: string;
    understand_distribution: string;
    apply_distribution: string;
    total_compliance: string;
    critical_chapters: string[];
    exam_strategy: string[];
  };
}

const SyllabusAnalyzer: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch syllabus data from backend
    fetch(`${API_CONFIG.BACKEND_URL}/api/syllabus`)
      .then(res => res.json())
      .then(data => {
        setSubjects(data.subjects || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading syllabus:', err);
        setLoading(false);
      });
  }, []);

  const toggleChapter = (chapterNumber: number) => {
    const newExpanded = new Set(expandedChapters);
    if (newExpanded.has(chapterNumber)) {
      newExpanded.delete(chapterNumber);
    } else {
      newExpanded.add(chapterNumber);
    }
    setExpandedChapters(newExpanded);
  };

  const toggleTopic = (topicId: string) => {
    const newExpanded = new Set(expandedTopics);
    if (newExpanded.has(topicId)) {
      newExpanded.delete(topicId);
    } else {
      newExpanded.add(topicId);
    }
    setExpandedTopics(newExpanded);
  };

  const getCoverageIcon = (coverage: string) => {
    if (coverage === 'Fully Covered') return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (coverage === 'Partially Covered') return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    return <XCircle className="w-5 h-5 text-red-500" />;
  };

  const getCoverageColor = (coverage: string) => {
    if (coverage === 'Fully Covered') return 'bg-green-50 border-green-200 text-green-700';
    if (coverage === 'Partially Covered') return 'bg-yellow-50 border-yellow-200 text-yellow-700';
    return 'bg-red-50 border-red-200 text-red-700';
  };

  const getPriorityColor = (priority: string) => {
    if (priority === 'Very High') return 'bg-red-100 text-red-700';
    if (priority === 'High') return 'bg-orange-100 text-orange-700';
    if (priority === 'Medium') return 'bg-blue-100 text-blue-700';
    return 'bg-gray-100 text-gray-700';
  };

  const getDepthColor = (depth: string) => {
    if (depth === 'Very High') return 'text-purple-600 font-bold';
    if (depth === 'High') return 'text-blue-600 font-semibold';
    if (depth === 'Medium') return 'text-gray-600';
    return 'text-gray-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.12),_transparent_34%),linear-gradient(135deg,_#f8fafc_0%,_#ffffff_55%,_#eef4ff_100%)] flex items-center justify-center px-4">
        <div className="w-full max-w-md rounded-3xl border border-white/70 bg-white/80 p-8 text-center shadow-2xl backdrop-blur-xl">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/30">
            <BookOpen className="h-7 w-7" />
          </div>
          <div className="mx-auto mb-4 h-2 w-24 overflow-hidden rounded-full bg-blue-100">
            <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-blue-600 to-purple-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Loading syllabus analysis</h2>
          <p className="mt-2 text-sm text-slate-600">Fetching subject, chapter, and RUA mapping data.</p>
        </div>
      </div>
    );
  }

  if (!selectedSubject) {
    return (
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.10),_transparent_32%),linear-gradient(180deg,_#f8fbff_0%,_#ffffff_58%,_#eef4ff_100%)] text-slate-900">
        <div className="border-b border-white/70 bg-white/75 backdrop-blur-xl">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            <Link to="/faculty-dashboard" className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:border-blue-200 hover:text-slate-900">
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </Link>
            <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700">
                  <Brain className="w-4 h-4" />
                  RUA Intelligence
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/20">
                    <BookOpen className="h-7 w-7" />
                  </div>
                  <h1 className="text-3xl font-black tracking-tight text-slate-900 sm:text-4xl md:text-5xl">
                    Syllabus & RUA Analysis
                  </h1>
                </div>
                <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
                  Review subject coverage, chapter weightage, and Remember-Understand-Apply mapping from a cleaner, more readable dashboard view.
                </p>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Coverage</div>
                  <div className="mt-2 text-2xl font-black text-blue-600">RUA</div>
                </div>
                <div className="rounded-2xl border border-purple-100 bg-white p-4 shadow-sm">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">View</div>
                  <div className="mt-2 text-2xl font-black text-purple-600">Topics</div>
                </div>
                <div className="rounded-2xl border border-green-100 bg-white p-4 shadow-sm">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Mode</div>
                  <div className="mt-2 text-2xl font-black text-green-600">AI</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="mb-12 rounded-3xl border border-white/70 bg-white/80 p-8 shadow-xl backdrop-blur-xl">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">Quick Overview</p>
                <h2 className="mt-2 text-2xl font-bold text-slate-900">What is RUA Analysis?</h2>
              </div>
              <p className="max-w-2xl text-sm leading-6 text-slate-600">
                Use this view to spot low-coverage topics and shape question papers around the right cognitive balance.
              </p>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-white p-6 shadow-sm transition-transform hover:-translate-y-1">
                <Book className="w-8 h-8 text-blue-600 mb-3" />
                <h3 className="font-bold text-lg mb-2">Remember</h3>
                <p className="text-gray-600 text-sm">Recall facts, definitions, and basic concepts. Foundation level knowledge.</p>
              </div>
              <div className="rounded-2xl border border-purple-100 bg-gradient-to-br from-purple-50 to-white p-6 shadow-sm transition-transform hover:-translate-y-1">
                <Brain className="w-8 h-8 text-purple-600 mb-3" />
                <h3 className="font-bold text-lg mb-2">Understand</h3>
                <p className="text-gray-600 text-sm">Explain, describe, and interpret concepts. Comprehension level.</p>
              </div>
              <div className="rounded-2xl border border-green-100 bg-gradient-to-br from-green-50 to-white p-6 shadow-sm transition-transform hover:-translate-y-1">
                <Lightbulb className="w-8 h-8 text-green-600 mb-3" />
                <h3 className="font-bold text-lg mb-2">Apply</h3>
                <p className="text-gray-600 text-sm">Use knowledge in new situations. Problem-solving and implementation.</p>
              </div>
            </div>
          </div>

          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Subjects</p>
              <h2 className="mt-2 text-2xl font-bold text-slate-900">Select a subject to analyze</h2>
            </div>
            <p className="hidden max-w-md text-sm text-slate-500 md:block">Pick a subject card to drill into chapter coverage, topics, and exam strategy.</p>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {subjects.map((subject) => (
              <div
                key={subject.subject_id}
                onClick={() => setSelectedSubject(subject)}
                className="group cursor-pointer rounded-3xl border border-white/70 bg-white/85 p-6 shadow-lg shadow-slate-200/60 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-2xl"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-md shadow-blue-500/20 transition-transform group-hover:scale-105">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <span className="rounded-full border border-purple-100 bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                    {subject.branch} - Sem {subject.semester}
                  </span>
                </div>
                <h3 className="mb-2 text-xl font-bold text-slate-900">{subject.subject_name}</h3>
                <div className="mb-5 flex flex-wrap items-center gap-3 text-sm text-slate-600">
                  <span className="rounded-full bg-slate-100 px-3 py-1">{subject.chapters.length} chapters</span>
                  <span className="rounded-full bg-slate-100 px-3 py-1">{subject.total_hours} hrs</span>
                  <span className="rounded-full bg-slate-100 px-3 py-1">{subject.total_credits} credits</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-blue-600">View analysis</span>
                  <ChevronRight className="w-5 h-5 text-slate-400 transition-all group-hover:translate-x-1 group-hover:text-blue-600" />
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.10),_transparent_30%),linear-gradient(180deg,_#f8fbff_0%,_#ffffff_58%,_#eef4ff_100%)] text-slate-900">
      <div className="sticky top-0 z-10 border-b border-white/70 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <button
            onClick={() => setSelectedSubject(null)}
            className="mb-4 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition-colors hover:border-blue-200 hover:text-slate-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Subjects
          </button>
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/20">
                <BookOpen className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">{selectedSubject.subject_name}</h1>
                <p className="text-sm text-slate-600">{selectedSubject.branch} • Semester {selectedSubject.semester} • {selectedSubject.total_hours} hours • {selectedSubject.total_credits} credits</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-2xl border border-blue-100 bg-white px-4 py-3 text-center shadow-sm">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Chapters</div>
                <div className="mt-1 text-lg font-bold text-blue-600">{selectedSubject.chapters.length}</div>
              </div>
              <div className="rounded-2xl border border-purple-100 bg-white px-4 py-3 text-center shadow-sm">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Hours</div>
                <div className="mt-1 text-lg font-bold text-purple-600">{selectedSubject.total_hours}</div>
              </div>
              <div className="rounded-2xl border border-green-100 bg-white px-4 py-3 text-center shadow-sm">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Credits</div>
                <div className="mt-1 text-lg font-bold text-green-600">{selectedSubject.total_credits}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Overall Analysis Cards */}
        {selectedSubject.overall_rua_analysis && (
          <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="rounded-3xl border border-blue-100 bg-white/85 p-6 shadow-lg shadow-slate-200/60 backdrop-blur-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-gray-900">Remember</h3>
                <Book className="w-6 h-6 text-blue-600" />
              </div>
              <p className="text-3xl font-bold text-blue-600">{selectedSubject.overall_rua_analysis.remember_distribution}</p>
              <p className="text-sm text-gray-600 mt-2">Foundation knowledge</p>
            </div>
            <div className="rounded-3xl border border-purple-100 bg-white/85 p-6 shadow-lg shadow-slate-200/60 backdrop-blur-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-gray-900">Understand</h3>
                <Brain className="w-6 h-6 text-purple-600" />
              </div>
              <p className="text-3xl font-bold text-purple-600">{selectedSubject.overall_rua_analysis.understand_distribution}</p>
              <p className="text-sm text-gray-600 mt-2">Concept comprehension</p>
            </div>
            <div className="rounded-3xl border border-green-100 bg-white/85 p-6 shadow-lg shadow-slate-200/60 backdrop-blur-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-gray-900">Apply</h3>
                <Lightbulb className="w-6 h-6 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-green-600">{selectedSubject.overall_rua_analysis.apply_distribution}</p>
              <p className="text-sm text-gray-600 mt-2">Practical application</p>
            </div>
          </div>
        )}

        {/* Exam Strategy */}
        {selectedSubject.overall_rua_analysis?.exam_strategy && (
          <div className="mb-8 rounded-3xl border border-orange-200 bg-gradient-to-r from-orange-50 to-red-50 p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <Target className="w-6 h-6 text-orange-600" />
              <h2 className="text-xl font-bold text-gray-900">📋 Exam Strategy</h2>
            </div>
            <ul className="space-y-2">
              {selectedSubject.overall_rua_analysis.exam_strategy.map((strategy, idx) => (
                <li key={idx} className="flex items-start gap-2 text-gray-700">
                  <TrendingUp className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                  <span>{strategy}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Chapter Breakdown */}
        <div className="space-y-4 pb-4">
          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Chapter Map</p>
              <h2 className="mt-2 text-2xl font-bold text-slate-900">Chapter-wise breakdown</h2>
            </div>
          </div>
          {selectedSubject.chapters.map((chapter) => (
            <div key={chapter.chapter_code} className="overflow-hidden rounded-3xl border border-white/70 bg-white/85 shadow-lg shadow-slate-200/50 backdrop-blur-xl">
              {/* Chapter Header */}
              <div
                onClick={() => toggleChapter(chapter.chapter_number)}
                className="cursor-pointer p-6 transition-colors hover:bg-slate-50/80"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-blue-600">Ch {chapter.chapter_number}</span>
                      <h3 className="text-xl font-bold text-gray-900">{chapter.chapter_name}</h3>
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {chapter.hours_allocated} hours
                      </span>
                      <span className="flex items-center gap-1">
                        <BarChart3 className="w-4 h-4" />
                        {chapter.weightage_percentage}% weightage
                      </span>
                      <span className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        {chapter.topics.length} topics
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {getCoverageIcon(chapter.rua_summary.remember_coverage)}
                      {getCoverageIcon(chapter.rua_summary.understand_coverage)}
                      {getCoverageIcon(chapter.rua_summary.apply_coverage)}
                    </div>
                    {expandedChapters.has(chapter.chapter_number) ? (
                      <ChevronDown className="w-6 h-6 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-6 h-6 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Chapter Content */}
              {expandedChapters.has(chapter.chapter_number) && (
                <div className="border-t border-slate-200 bg-slate-50/70 p-6">
                  {/* Learning Objectives */}
                  <div className="mb-6">
                    <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                      <Target className="w-5 h-5 text-blue-600" />
                      Learning Objectives
                    </h4>
                    <ul className="space-y-2">
                      {chapter.learning_objectives.map((obj, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-gray-700">
                          <span className="text-blue-600 font-bold">•</span>
                          {obj}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* RUA Summary */}
                    <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div className={`rounded-2xl border p-4 ${getCoverageColor(chapter.rua_summary.remember_coverage)}`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold">Remember</span>
                        {getCoverageIcon(chapter.rua_summary.remember_coverage)}
                      </div>
                      <p className="text-sm">{chapter.rua_summary.remember_coverage}</p>
                    </div>
                    <div className={`rounded-2xl border p-4 ${getCoverageColor(chapter.rua_summary.understand_coverage)}`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold">Understand</span>
                        {getCoverageIcon(chapter.rua_summary.understand_coverage)}
                      </div>
                      <p className="text-sm">{chapter.rua_summary.understand_coverage}</p>
                    </div>
                    <div className={`rounded-2xl border p-4 ${getCoverageColor(chapter.rua_summary.apply_coverage)}`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold">Apply</span>
                        {getCoverageIcon(chapter.rua_summary.apply_coverage)}
                      </div>
                      <p className="text-sm">{chapter.rua_summary.apply_coverage}</p>
                    </div>
                  </div>

                  {/* Recommendations */}
                  {chapter.rua_summary.recommendations.length > 0 && (
                    <div className="mb-6 rounded-2xl border border-blue-200 bg-blue-50 p-4">
                      <h4 className="font-bold text-blue-900 mb-2 flex items-center gap-2">
                        <Award className="w-5 h-5" />
                        Recommendations
                      </h4>
                      <ul className="space-y-1">
                        {chapter.rua_summary.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                            <span className="text-blue-600">▸</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Topics */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-gray-900">Topics & Subtopics</h4>
                    {chapter.topics.map((topic) => (
                      <div key={topic.topic_id} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                        <div
                          onClick={() => toggleTopic(topic.topic_id)}
                          className="cursor-pointer p-4 transition-colors hover:bg-slate-50"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h5 className="font-bold text-gray-900 mb-1">{topic.topic_name}</h5>
                              <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                                {topic.focus_type}
                              </span>
                            </div>
                            {expandedTopics.has(topic.topic_id) ? (
                              <ChevronDown className="w-5 h-5 text-gray-400" />
                            ) : (
                              <ChevronRight className="w-5 h-5 text-gray-400" />
                            )}
                          </div>
                        </div>

                        {expandedTopics.has(topic.topic_id) && (
                          <div className="border-t border-slate-200 bg-slate-50 p-4">
                            {/* Subtopics */}
                            <div className="mb-4">
                              <h6 className="text-sm font-bold text-gray-700 mb-2">Subtopics:</h6>
                              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {topic.subtopics.map((subtopic, idx) => (
                                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                                    <span className="text-blue-500">→</span>
                                    {subtopic}
                                  </li>
                                ))}
                              </ul>
                            </div>

                            {/* RUA Mapping */}
                            <div className="space-y-3">
                              {Object.entries(topic.rua_mapping).map(([level, data]) => (
                                <div key={level} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                                  <div className="flex items-center justify-between mb-3">
                                    <h6 className="font-bold text-gray-900 capitalize">{level}</h6>
                                    <div className="flex items-center gap-2">
                                      <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(data.exam_priority)}`}>
                                        {data.exam_priority} Priority
                                      </span>
                                      <span className={`text-sm ${getDepthColor(data.depth)}`}>
                                        {data.depth} Depth
                                      </span>
                                    </div>
                                  </div>
                                  
                                  <div className="space-y-2 text-sm">
                                    <div>
                                      <span className="font-medium text-gray-700">Concepts:</span>
                                      <ul className="mt-1 space-y-1">
                                        {data.concepts.map((concept, idx) => (
                                          <li key={idx} className="text-gray-600 ml-4 flex items-start gap-2">
                                            <span className="text-blue-500">•</span>
                                            {concept}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                    
                                    <div className="flex items-center gap-4 pt-2 border-t border-gray-100">
                                      <span className="text-gray-700">
                                        <strong>Marks:</strong> {data.typical_marks}
                                      </span>
                                      <span className="text-gray-700">
                                        <strong>Questions:</strong> {data.question_types.join(', ')}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default SyllabusAnalyzer;
