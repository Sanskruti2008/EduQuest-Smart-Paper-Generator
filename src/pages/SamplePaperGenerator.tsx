import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, Zap,Download, RefreshCw, Settings, BookOpen, Target, TrendingUp, Calendar, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useQuestionBank } from '../context/QuestionBankContext';
import { BRANCHES, SEMESTERS, formatBranchSemester } from '../utils/constants';
import { 
  generateMSBTEPaper, 
  type ChapterWeightage, 
  type GeneratedSection 
} from '../utils/paperGenerationLogic';

interface GeneratedPaper {
  id: string;
  title: string;
  subject: string;
  grade: string;
  totalMarks: number;
  duration: string;
  sections: GeneratedSection[];
  difficultyDistribution: {
    easy: number;
    medium: number;
    hard: number;
  };
  bloomDistribution?: Map<string, number>;
  chapterDistribution?: Map<string, number>;
  generatedAt: Date;
}

const SamplePaperGenerator = () => {
  const { questions } = useQuestionBank();
  
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [totalMarks, setTotalMarks] = useState('100');
  const [difficulty, setDifficulty] = useState('balanced');
  const [format, setFormat] = useState('msbte');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPaper, setGeneratedPaper] = useState<GeneratedPaper | null>(null);

  // Get unique values from question bank
  const selectedGrade = selectedBranch && selectedSemester ? formatBranchSemester(selectedBranch, selectedSemester) : '';
  const subjects = selectedGrade 
    ? Array.from(new Set(questions.filter(q => q.grade === selectedGrade).map(q => q.subject)))
    : [];
  const years = ['2024', '2023', '2022', '2021', '2020'];

  const generatePaper = () => {
    if (!selectedGrade || !selectedSubject) {
      alert('Please select branch, semester, and subject');
      return;
    }

    setIsGenerating(true);

    // Filter questions based on selection
    const filteredQuestions = questions.filter(q => 
      q.grade === selectedGrade && 
      q.subject === selectedSubject &&
      (selectedYear ? q.year === selectedYear : true)
    );

    if (filteredQuestions.length === 0) {
      alert('No questions available for selected criteria');
      setIsGenerating(false);
      return;
    }

    console.log('📚 Generating paper with improved logic...');
    console.log('   Available questions:', filteredQuestions.length);
    
    // Log question marks distribution
    const marksCounts = filteredQuestions.reduce((acc, q) => {
      acc[q.marks] = (acc[q.marks] || 0) + 1;
      return acc;
    }, {} as Record<number, number>);
    console.log('   Questions by marks:', marksCounts);
    console.log('   Need: 7 × 2-mark questions, 20 × 4-mark questions');
    
    const twoMarkQuestions = filteredQuestions.filter(q => q.marks === 2);
    const fourMarkQuestions = filteredQuestions.filter(q => q.marks === 4);
    console.log(`   Available: ${twoMarkQuestions.length} × 2-mark, ${fourMarkQuestions.length} × 4-mark`);
    
    if (twoMarkQuestions.length < 7) {
      alert(`⚠️ Need at least 7 two-mark questions, but only ${twoMarkQuestions.length} available.\n\nPlease add more 2-mark questions to the Question Bank.`);
      setIsGenerating(false);
      return;
    }
    
    if (fourMarkQuestions.length < 20) {
      alert(`⚠️ Need at least 20 four-mark questions, but only ${fourMarkQuestions.length} available.\n\nPlease add more 4-mark questions to the Question Bank.`);
      setIsGenerating(false);
      return;
    }
    
    // Simulate AI processing
    setTimeout(() => {
      // Extract unique chapters from questions
      const uniqueChapters = Array.from(new Set(filteredQuestions.map(q => q.chapter)));
      
      // Create chapter weightages
      // In a real scenario, this would come from syllabus data
      const chapterWeightages: ChapterWeightage[] = uniqueChapters.map((chapter, idx) => {
        // Calculate priority based on question availability
        const chapterQs = filteredQuestions.filter(q => q.chapter === chapter);
        const priority = chapterQs.length > 10 ? 'High' : 
                        chapterQs.length > 5 ? 'Medium' : 'Low';
        
        return {
          chapter,
          weightage: Math.round(100 / uniqueChapters.length), // Equal distribution
          priority: priority as 'Very High' | 'High' | 'Medium' | 'Low'
        };
      });
      
      console.log('   Chapter weightages:', chapterWeightages);
      
      // Generate using improved logic
      const result = generateMSBTEPaper(filteredQuestions, chapterWeightages);
      
      console.log('✅ Paper generated:');
      console.log('   Total marks:', result.totalMarks);
      console.log('   Sections:', result.sections.length);
      console.log('   Chapter distribution:', Object.fromEntries(result.chapterDistribution));
      console.log('   Bloom distribution:', Object.fromEntries(result.bloomDistribution));
      console.log('   Difficulty distribution:', Object.fromEntries(result.difficultyDistribution));
      
      // Calculate difficulty distribution
      const difficultyDist = {
        easy: result.difficultyDistribution.get('Easy') || 0,
        medium: result.difficultyDistribution.get('Medium') || 0,
        hard: result.difficultyDistribution.get('Hard') || 0
      };

      const paper: GeneratedPaper = {
        id: `PAPER-${Date.now()}`,
        title: `${selectedSubject} - Sample Paper ${selectedYear || 'Latest'}`,
        subject: selectedSubject,
        grade: selectedGrade,
        totalMarks: result.totalMarks,
        duration: '3 hours',
        sections: result.sections,
        difficultyDistribution: difficultyDist,
        bloomDistribution: result.bloomDistribution,
        chapterDistribution: result.chapterDistribution,
        generatedAt: new Date()
      };

      setGeneratedPaper(paper);
      setIsGenerating(false);
    }, 2000);
  };

  const downloadPaper = () => {
    if (!generatedPaper) return;
    
    // Create a formatted text version for download
    const paperContent = `
${generatedPaper.title}
Grade: ${generatedPaper.grade}
Total Marks: ${generatedPaper.totalMarks}
Duration: ${generatedPaper.duration}
Generated on: ${generatedPaper.generatedAt.toLocaleDateString()}

${'='.repeat(80)}

${generatedPaper.sections.map((section) => `
${section.name}
${section.instructions}
Total Marks: ${section.totalMarks}
${'-'.repeat(80)}

${section.questions.map((q, qIdx) => `
Q${qIdx + 1}. ${q.text} (${q.marks} marks)
Chapter: ${q.chapter}
Difficulty: ${q.difficulty}
`).join('\n')}
`).join('\n\n')}

${'='.repeat(80)}

Difficulty Distribution:
Easy: ${generatedPaper.difficultyDistribution.easy} questions
Medium: ${generatedPaper.difficultyDistribution.medium} questions
Hard: ${generatedPaper.difficultyDistribution.hard} questions
`;

    const blob = new Blob([paperContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${generatedPaper.title.replace(/\s+/g, '_')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-purple-50/30">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link to="/student-dashboard" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                AI Sample Paper Generator
              </h1>
              <p className="text-gray-600 mt-1">Auto-generate practice papers based on MSBTE format & curriculum</p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!generatedPaper ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Configuration Panel */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 shadow-lg">
                <div className="flex items-center gap-3 mb-6">
                  <Settings className="w-6 h-6 text-purple-600" />
                  <h2 className="text-2xl font-bold text-gray-900">Paper Configuration</h2>
                </div>

                <div className="space-y-6">
                  {/* Branch & Semester Selection */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Branch
                      </label>
                      <select
                        value={selectedBranch}
                        onChange={(e) => {
                          setSelectedBranch(e.target.value);
                          setSelectedSemester('');
                          setSelectedSubject('');
                        }}
                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all"
                      >
                        <option value="">Select Branch</option>
                        {BRANCHES.map(branch => (
                          <option key={branch} value={branch}>{branch}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Semester
                      </label>
                      <select
                        value={selectedSemester}
                        onChange={(e) => {
                          setSelectedSemester(e.target.value);
                          setSelectedSubject('');
                        }}
                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all"
                      >
                        <option value="">Select Semester</option>
                        {SEMESTERS.map(semester => (
                          <option key={semester} value={semester}>{semester}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Subject Selection */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Subject
                    </label>
                    <select
                      value={selectedSubject}
                      onChange={(e) => setSelectedSubject(e.target.value)}
                      disabled={!selectedGrade}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all disabled:bg-gray-100"
                    >
                      <option value="">Select Subject</option>
                      {subjects.map(subject => (
                        <option key={subject} value={subject}>{subject}</option>
                      ))}
                    </select>
                  </div>

                  {/* Year Selection */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Focus on Year (Optional)
                    </label>
                    <select
                      value={selectedYear}
                      onChange={(e) => setSelectedYear(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all"
                    >
                      <option value="">All Years</option>
                      {years.map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>

                  {/* Total Marks */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Total Marks
                    </label>
                    <select
                      value={totalMarks}
                      onChange={(e) => setTotalMarks(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all"
                    >
                      <option value="60">60 Marks</option>
                      <option value="80">80 Marks</option>
                      <option value="100">100 Marks</option>
                    </select>
                  </div>

                  {/* Difficulty Level */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Difficulty Level
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {['easy', 'balanced', 'hard'].map(level => (
                        <button
                          key={level}
                          onClick={() => setDifficulty(level)}
                          className={`px-4 py-3 rounded-lg font-medium transition-all ${
                            difficulty === level
                              ? 'bg-purple-600 text-white shadow-lg'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {level.charAt(0).toUpperCase() + level.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Format */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Paper Format
                    </label>
                    <select
                      value={format}
                      onChange={(e) => setFormat(e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all"
                    >
                      <option value="msbte">MSBTE Format</option>
                      <option value="cbse">CBSE Format (Coming Soon)</option>
                      <option value="icse">ICSE Format (Coming Soon)</option>
                    </select>
                  </div>
                </div>

                {/* Generate Button */}
                <button
                  onClick={generatePaper}
                  disabled={isGenerating || !selectedGrade || !selectedSubject}
                  className={`w-full mt-8 py-4 rounded-xl font-bold text-lg transition-all ${
                    isGenerating || !selectedGrade || !selectedSubject
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 shadow-lg hover:shadow-xl'
                  }`}
                >
                  {isGenerating ? (
                    <span className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Generating Paper...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <Zap className="w-5 h-5" />
                      Generate Sample Paper
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Features Panel */}
            <div className="space-y-6">
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4">AI Features</h3>
                <div className="space-y-3">
                  {[
                    { icon: Target, text: 'MSBTE Format Matching' },
                    { icon: TrendingUp, text: 'Smart Difficulty Distribution' },
                    { icon: BookOpen, text: 'Curriculum-Based Selection' },
                    { icon: Calendar, text: 'PYQ Pattern Analysis' }
                  ].map((feature, idx) => (
                    <div key={idx} className="flex items-center gap-3 text-gray-700">
                      <feature.icon className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-medium">{feature.text}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border-2 border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4">MSBTE Format</h3>
                <div className="space-y-4 text-sm text-gray-600">
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Section A (20%)</div>
                    <div>Multiple Choice Questions - 1 mark each</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Section B (30%)</div>
                    <div>Short Answer Questions - 3 marks each</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Section C (50%)</div>
                    <div>Long Answer Questions - 10 marks each</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Generated Paper Display */
          <div className="space-y-8">
            {/* Paper Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl p-8 border-2 border-green-200 shadow-lg"
            >
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <h2 className="text-3xl font-bold text-gray-900">{generatedPaper.title}</h2>
                  </div>
                  <p className="text-gray-600">Generated on {generatedPaper.generatedAt.toLocaleDateString()}</p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setGeneratedPaper(null)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all font-medium"
                  >
                    Generate New
                  </button>
                  <button
                    onClick={downloadPaper}
                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all font-medium flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-gray-50 rounded-xl p-4">
                <div>
                  <div className="text-sm text-gray-600 mb-1">Grade</div>
                  <div className="font-bold text-gray-900">{generatedPaper.grade}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Total Marks</div>
                  <div className="font-bold text-gray-900">{generatedPaper.totalMarks}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Duration</div>
                  <div className="font-bold text-gray-900">{generatedPaper.duration}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Format</div>
                  <div className="font-bold text-gray-900">MSBTE</div>
                </div>
              </div>
            </motion.div>

            {/* Difficulty Distribution */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl p-6 border-2 border-gray-200"
            >
              <h3 className="text-xl font-bold text-gray-900 mb-4">Difficulty Distribution</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg border-2 border-green-200">
                  <div className="text-3xl font-bold text-green-700">{generatedPaper.difficultyDistribution.easy}</div>
                  <div className="text-sm text-green-600 font-medium mt-1">Easy Questions</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
                  <div className="text-3xl font-bold text-yellow-700">{generatedPaper.difficultyDistribution.medium}</div>
                  <div className="text-sm text-yellow-600 font-medium mt-1">Medium Questions</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg border-2 border-red-200">
                  <div className="text-3xl font-bold text-red-700">{generatedPaper.difficultyDistribution.hard}</div>
                  <div className="text-sm text-red-600 font-medium mt-1">Hard Questions</div>
                </div>
              </div>
            </motion.div>

            {/* Bloom's Taxonomy Distribution */}
            {generatedPaper.bloomDistribution && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="bg-white rounded-2xl p-6 border-2 border-gray-200"
              >
                <h3 className="text-xl font-bold text-gray-900 mb-4">Bloom's Taxonomy Distribution</h3>
                <div className="space-y-3">
                  {Array.from(generatedPaper.bloomDistribution.entries())
                    .filter(([_, marks]) => marks > 0)
                    .map(([level, marks]) => {
                      const colors = {
                        'Remember': { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', bar: 'bg-blue-500' },
                        'Understand': { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-700', bar: 'bg-indigo-500' },
                        'Apply': { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', bar: 'bg-purple-500' },
                        'Analyze': { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-700', bar: 'bg-pink-500' },
                        'Evaluate': { bg: 'bg-rose-50', border: 'border-rose-200', text: 'text-rose-700', bar: 'bg-rose-500' },
                        'Create': { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', bar: 'bg-red-500' }
                      };
                      const color = colors[level] || colors['Understand'];
                      const percentage = ((marks / generatedPaper.totalMarks) * 100).toFixed(1);

                      return (
                        <div key={level} className={`p-4 ${color.bg} rounded-lg border-2 ${color.border}`}>
                          <div className="flex justify-between items-center mb-2">
                            <span className={`font-semibold ${color.text}`}>{level}</span>
                            <span className={`text-sm font-bold ${color.text}`}>{marks} marks ({percentage}%)</span>
                          </div>
                          <div className="w-full bg-white rounded-full h-2">
                            <div className={`h-2 rounded-full ${color.bar}`} style={{ width: `${percentage}%` }}></div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </motion.div>
            )}

            {/* Chapter Distribution */}
            {generatedPaper.chapterDistribution && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-2xl p-6 border-2 border-gray-200"
              >
                <h3 className="text-xl font-bold text-gray-900 mb-4">Chapter Coverage</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Array.from(generatedPaper.chapterDistribution.entries())
                    .sort((a, b) => b[1] - a[1])
                    .map(([chapter, count]) => (
                      <div key={chapter} className="p-3 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border-2 border-purple-200">
                        <div className="text-sm text-gray-600 mb-1 truncate" title={chapter}>{chapter}</div>
                        <div className="text-2xl font-bold text-purple-700">{count}</div>
                        <div className="text-xs text-purple-600">question{count !== 1 ? 's' : ''}</div>
                      </div>
                    ))}
                </div>
              </motion.div>
            )}

            {/* Sections */}
            {generatedPaper.sections.map((section, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + idx * 0.1 }}
                className="bg-white rounded-2xl p-8 border-2 border-gray-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{section.name}</h3>
                    <p className="text-sm text-gray-600 italic">{section.instructions}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Total Marks</div>
                    <div className="text-2xl font-bold text-purple-600">{section.totalMarks}</div>
                  </div>
                </div>

                <div className="space-y-4 mt-6">
                  {section.questions.map((question, qIdx) => (
                    <div key={qIdx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900 mb-1">
                            Q{question.questionNumber}. {question.text}
                          </div>
                          <div className="flex items-center gap-3 mt-2">
                            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">
                              {question.chapter}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded font-medium ${
                              question.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                              question.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {question.difficulty}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4 px-3 py-1 bg-purple-100 text-purple-700 rounded font-bold text-sm">
                          {question.marks} marks
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default SamplePaperGenerator;
