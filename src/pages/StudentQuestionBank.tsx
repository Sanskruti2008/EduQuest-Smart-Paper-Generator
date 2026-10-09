import { Fragment, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Header from '../components/Header';
import { useQuestionBank, Question } from '../context/QuestionBankContext';
import { BRANCHES, SEMESTERS, formatBranchSemester } from '../utils/constants';
import { Search, Filter, BookOpen, MessageSquare, Send, ThumbsUp, ThumbsDown, X, Loader2 } from 'lucide-react';

const StudentQuestionBank = () => {
  const { questions, loading, fetchDbQuestions, addFeedback } = useQuestionBank();
  
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  const [selectedSemester, setSelectedSemester] = useState<string | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);

  // Fetch DB questions whenever branch + semester are both chosen
  useEffect(() => {
    if (selectedBranch && selectedSemester) {
      fetchDbQuestions(selectedBranch, selectedSemester);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBranch, selectedSemester]);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('all');
  
  // Feedback modal state
  const [feedbackModal, setFeedbackModal] = useState<{ isOpen: boolean; question: Question | null }>({
    isOpen: false,
    question: null
  });
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackType, setFeedbackType] = useState<'positive' | 'negative' | 'suggestion'>('suggestion');

  // Get unique values
  const selectedGrade = selectedBranch && selectedSemester ? formatBranchSemester(selectedBranch, selectedSemester) : null;
  const subjects = selectedGrade
    ? Array.from(new Set(questions.filter(q => q.grade === selectedGrade).map(q => q.subject)))
    : [];

  const filteredQuestions = selectedGrade && selectedSubject
    ? questions.filter(q => {
        const matchesGrade = q.grade === selectedGrade;
        const matchesSubject = q.subject === selectedSubject;
        const matchesSearch = searchTerm === '' || 
                             q.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             q.chapter.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesDifficulty = difficultyFilter === 'all' || q.difficulty === difficultyFilter;
        return matchesGrade && matchesSubject && matchesSearch && matchesDifficulty;
      })
    : [];

  const handleOpenFeedback = (question: Question) => {
    setFeedbackModal({ isOpen: true, question });
    setFeedbackText('');
    setFeedbackType('suggestion');
  };

  const handleCloseFeedback = () => {
    setFeedbackModal({ isOpen: false, question: null });
    setFeedbackText('');
  };

  const handleSubmitFeedback = () => {
    if (feedbackModal.question && feedbackText.trim()) {
      addFeedback({
        questionId: feedbackModal.question.id,
        questionText: feedbackModal.question.text,
        subject: feedbackModal.question.subject,
        type: feedbackType,
        message: feedbackText.trim(),
        createdAt: new Date().toISOString()
      });
      handleCloseFeedback();
      alert('Thank you for your feedback! It has been sent to the faculty.');
    }
  };

  const stats = {
    total: filteredQuestions.length,
    easy: filteredQuestions.filter(q => q.difficulty === 'Easy').length,
    medium: filteredQuestions.filter(q => q.difficulty === 'Medium').length,
    hard: filteredQuestions.filter(q => q.difficulty === 'Hard').length,
  };

  // Show selection interface if not all selections are made
  if (!selectedBranch || !selectedSemester || !selectedSubject) {
    const selectionSteps = [
      { label: 'Select Branch', active: !!selectedBranch },
      { label: 'Select Semester', active: !!selectedSemester },
      { label: 'Select Subject', active: !!selectedSubject }
    ];

    return (
      <div className="min-h-screen bg-white">
        <Header title="Question Bank" />
        
        <main className="max-w-5xl mx-auto px-4 py-12 md:py-20">
          <div className="text-center mb-16">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Browse Questions</h1>
            <p className="text-gray-600 text-lg">Choose branch, semester, and subject to view questions</p>
          </div>

          <div className="space-y-8">
            <div className="flex items-center justify-center gap-4 flex-wrap mb-8">
              {selectionSteps.map((step, index) => (
                <Fragment key={step.label}>
                  <div
                    className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all ${
                      step.active ? 'bg-green-600 text-white shadow-lg' : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    <span className="w-6 h-6 rounded-full bg-white flex items-center justify-center text-sm font-bold text-gray-900">
                      {index + 1}
                    </span>
                    <span className="font-medium">{step.label}</span>
                  </div>
                  {index < selectionSteps.length - 1 && (
                    <div className="w-8 h-0.5 bg-gray-300"></div>
                  )}
                </Fragment>
              ))}
            </div>

            {/* Branch Selection */}
            {!selectedBranch && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm"
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center font-bold text-sm">
                    1
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">Select Branch</h3>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {BRANCHES.map(branch => (
                    <button
                      key={branch}
                      onClick={() => {
                        setSelectedBranch(branch);
                        setSelectedSemester(null);
                        setSelectedSubject(null);
                      }}
                      className={`p-5 rounded-xl border-2 font-bold text-lg transition-all ${
                        selectedBranch === branch
                          ? 'border-green-600 bg-green-600 text-white shadow-lg scale-105'
                          : 'border-gray-200 hover:border-green-400 hover:shadow-md text-gray-700'
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
                className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm"
              >
                <button
                  onClick={() => {
                    setSelectedBranch(null);
                    setSelectedSemester(null);
                    setSelectedSubject(null);
                  }}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium mb-6"
                >
                  <span className="w-4 h-4 rounded-full border border-gray-400 flex items-center justify-center">&larr;</span>
                  Change Branch
                </button>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center font-bold text-sm">
                    2
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Select Semester</h3>
                    <p className="text-sm text-gray-600">Branch: {selectedBranch}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {SEMESTERS.map(semester => (
                    <button
                      key={semester}
                      onClick={() => {
                        setSelectedSemester(semester);
                        setSelectedSubject(null);
                      }}
                      className={`p-5 rounded-xl border-2 font-bold text-lg transition-all ${
                        selectedSemester === semester
                          ? 'border-green-600 bg-green-600 text-white shadow-lg scale-105'
                          : 'border-gray-200 hover:border-green-400 hover:shadow-md text-gray-700'
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
                className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm"
              >
                <div className="flex flex-wrap items-center gap-4 mb-6">
                  <button
                    onClick={() => {
                      setSelectedSemester(null);
                      setSelectedSubject(null);
                    }}
                    className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium"
                  >
                    <span className="w-4 h-4 rounded-full border border-gray-400 flex items-center justify-center">&larr;</span>
                    Change Semester
                  </button>
                  <button
                    onClick={() => {
                      setSelectedBranch(null);
                      setSelectedSemester(null);
                      setSelectedSubject(null);
                    }}
                    className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium"
                  >
                    <span className="w-4 h-4 rounded-full border border-gray-400 flex items-center justify-center">&larr;</span>
                    Start Over
                  </button>
                </div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center font-bold text-sm">
                    3
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Select Subject</h3>
                    <p className="text-sm text-gray-600">{selectedGrade}</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {subjects.map(subject => (
                    <button
                      key={subject}
                      onClick={() => setSelectedSubject(subject)}
                      className={`p-5 rounded-xl border-2 font-bold text-lg transition-all text-left ${
                        selectedSubject === subject
                          ? 'border-green-600 bg-green-600 text-white shadow-lg scale-105'
                          : 'border-gray-200 hover:border-green-400 hover:shadow-md text-gray-700'
                      }`}
                    >
                      {subject}
                    </button>
                  ))}
                </div>
                {subjects.length === 0 && (
                  <div className="text-center text-gray-500 mt-6">
                    {loading
                      ? <span className="flex items-center justify-center gap-2"><Loader2 className="w-5 h-5 animate-spin" /> Loading subjects from database…</span>
                      : 'No subjects available yet for this branch and semester.'}
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
    <div className="min-h-screen bg-white">
      <Header title="Question Bank" />

      {/* Stats Bar */}
      <div className="bg-green-50 border-y border-green-200 py-8">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-gray-900">{stats.total}</div>
              <div className="text-sm text-gray-600 font-medium mt-2">Total Questions</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-green-600">{stats.easy}</div>
              <div className="text-sm text-gray-600 font-medium mt-2">Easy</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-yellow-600">{stats.medium}</div>
              <div className="text-sm text-gray-600 font-medium mt-2">Medium</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-red-600">{stats.hard}</div>
              <div className="text-sm text-gray-600 font-medium mt-2">Hard</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Current Selection Banner */}
        <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="text-xs uppercase tracking-wider text-green-100 mb-2">Current Selection</div>
              <div className="font-bold text-xl">
                {selectedGrade} • {selectedSubject}
              </div>
            </div>
            <button
              onClick={() => {
                setSelectedBranch(null);
                setSelectedSemester(null);
                setSelectedSubject(null);
              }}
              className="px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-white font-semibold transition-all"
            >
              Change Selection
            </button>
          </div>
        </div>

        {/* Header */}
        <div className="flex flex-col md:flex-row gap-4 mb-8 items-start md:items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Practice Questions</h1>
            <p className="text-gray-600">Browse questions and provide feedback to help improve the question bank</p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-xl border border-blue-200">
            <MessageSquare className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-700">Click on any question to give feedback</span>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl p-6 border border-gray-200 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search questions..."
                className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 focus:border-green-400 focus:ring-2 focus:ring-green-100 outline-none transition-all"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 focus:border-green-400 focus:ring-2 focus:ring-green-100 outline-none transition-all appearance-none bg-white"
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value)}
              >
                <option value="all">All Difficulties</option>
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
          </div>
        </div>

        {/* Questions List */}
        <div className="space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-white rounded-2xl border border-gray-200">
              <Loader2 className="w-12 h-12 text-gray-400 animate-spin mb-4" />
              <p className="text-gray-500 font-medium">Loading questions from database…</p>
            </div>
          ) : filteredQuestions.length === 0 ? (
            <div className="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-gray-300">
              <BookOpen className="w-20 h-20 text-gray-300 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-gray-700 mb-2">No questions found</h3>
              <p className="text-gray-500">Try adjusting your filters or check back later</p>
            </div>
          ) : (
            filteredQuestions.map((question, index) => (
              <motion.div
                key={question.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg hover:border-green-300 transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-4 flex-wrap">
                      <span className={`px-3 py-1 rounded-lg text-xs font-bold ${
                        question.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                        question.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {question.difficulty}
                      </span>
                      <span className="px-3 py-1 rounded-lg text-xs font-bold bg-blue-100 text-blue-700">
                        {question.marks}M
                      </span>
                      <span className="px-3 py-1 rounded-lg text-xs font-bold bg-purple-100 text-purple-700">
                        {question.type}
                      </span>
                      <span className="text-sm text-gray-500 font-medium">
                        {question.subject} • {question.chapter}
                      </span>
                    </div>
                    <p className="text-gray-800 leading-relaxed mb-4 text-base">{question.text}</p>
                    {question.image && (
                      <div className="mb-4">
                        <img 
                          src={question.image} 
                          alt="Question illustration" 
                          className="max-w-full max-h-64 rounded-lg border border-gray-200 object-contain"
                        />
                      </div>
                    )}
                    {question.tags && question.tags.length > 0 && (
                      <div className="flex gap-2 flex-wrap">
                        {question.tags.map((tag, i) => (
                          <span key={i} className="text-xs text-gray-600 bg-gray-100 px-3 py-1 rounded-lg font-medium">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button 
                    onClick={() => handleOpenFeedback(question)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-600 transition-all font-medium"
                    title="Give Feedback"
                  >
                    <MessageSquare className="w-4 h-4" />
                    Feedback
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </main>

      {/* Feedback Modal */}
      {feedbackModal.isOpen && feedbackModal.question && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900">Give Feedback</h3>
              <button
                onClick={handleCloseFeedback}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Question Preview */}
            <div className="bg-gray-50 rounded-xl p-4 mb-6">
              <p className="text-sm text-gray-600 mb-2">Question:</p>
              <p className="text-gray-800 font-medium">{feedbackModal.question.text}</p>
            </div>

            {/* Feedback Type */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">Feedback Type</label>
              <div className="flex gap-3">
                <button
                  onClick={() => setFeedbackType('positive')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 transition-all ${
                    feedbackType === 'positive'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  <ThumbsUp className="w-4 h-4" />
                  Helpful
                </button>
                <button
                  onClick={() => setFeedbackType('negative')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 transition-all ${
                    feedbackType === 'negative'
                      ? 'border-red-500 bg-red-50 text-red-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  <ThumbsDown className="w-4 h-4" />
                  Issue
                </button>
                <button
                  onClick={() => setFeedbackType('suggestion')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 transition-all ${
                    feedbackType === 'suggestion'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  Suggestion
                </button>
              </div>
            </div>

            {/* Feedback Text */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Your Feedback</label>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="Share your thoughts about this question..."
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 outline-none transition-all resize-none"
                rows={4}
              />
            </div>

            {/* Submit Button */}
            <div className="flex justify-end gap-3">
              <button
                onClick={handleCloseFeedback}
                className="px-5 py-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 text-gray-700 font-medium transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitFeedback}
                disabled={!feedbackText.trim()}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium transition-all"
              >
                <Send className="w-4 h-4" />
                Submit Feedback
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default StudentQuestionBank;
