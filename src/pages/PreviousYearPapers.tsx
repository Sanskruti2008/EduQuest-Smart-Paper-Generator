import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Download, Eye, Calendar, BookOpen, Filter, Search, FileText } from 'lucide-react';
import { motion } from 'framer-motion';
import { BRANCHES, SEMESTERS, formatBranchSemester } from '../utils/constants';

// Sample previous year papers data (would come from admin uploads)
const previousPapers = [
  {
    id: 1,
    title: 'Mathematics Final Exam 2024',
    subject: 'Mathematics',
    grade: formatBranchSemester('Computer Technology', '5th Semester'),
    year: '2024',
    examType: 'Final',
    totalMarks: 100,
    duration: '3 hours',
    uploadedBy: 'Admin',
    uploadDate: '2024-12-15',
    downloadUrl: '#'
  },
  {
    id: 2,
    title: 'Physics Mid-Term 2024',
    subject: 'Physics',
    grade: formatBranchSemester('Information Technology', '4th Semester'),
    year: '2024',
    examType: 'Mid-Term',
    totalMarks: 80,
    duration: '2.5 hours',
    uploadedBy: 'Admin',
    uploadDate: '2024-11-20',
    downloadUrl: '#'
  },
  {
    id: 3,
    title: 'Chemistry Annual Exam 2023',
    subject: 'Chemistry',
    grade: formatBranchSemester('Civil Engineering', '6th Semester'),
    year: '2023',
    examType: 'Annual',
    totalMarks: 100,
    duration: '3 hours',
    uploadedBy: 'Admin',
    uploadDate: '2024-10-10',
    downloadUrl: '#'
  },
  {
    id: 4,
    title: 'Biology Final Exam 2024',
    subject: 'Biology',
    grade: formatBranchSemester('Automobile Engineering', '3rd Semester'),
    year: '2024',
    examType: 'Final',
    totalMarks: 100,
    duration: '3 hours',
    uploadedBy: 'Admin',
    uploadDate: '2024-12-01',
    downloadUrl: '#'
  },
  {
    id: 5,
    title: 'English Literature 2023',
    subject: 'English',
    grade: formatBranchSemester('Dress Designing & Garment Manufacturing', '2nd Semester'),
    year: '2023',
    examType: 'Annual',
    totalMarks: 100,
    duration: '3 hours',
    uploadedBy: 'Admin',
    uploadDate: '2024-09-15',
    downloadUrl: '#'
  },
  {
    id: 6,
    title: 'Computer Science 2024',
    subject: 'Computer Science',
    grade: formatBranchSemester('Interior Designing', '1st Semester'),
    year: '2024',
    examType: 'Final',
    totalMarks: 100,
    duration: '3 hours',
    uploadedBy: 'Admin',
    uploadDate: '2024-12-10',
    downloadUrl: '#'
  }
];

const PreviousYearPapers = () => {
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedYear, setSelectedYear] = useState('all');

  const years = [...new Set(previousPapers.map(p => p.year))];

  const selectedGrade = selectedBranch && selectedSemester ? formatBranchSemester(selectedBranch, selectedSemester) : '';

  // Get available subjects for selected branch + semester
  const availableSubjects = selectedGrade 
    ? [...new Set(previousPapers.filter(p => p.grade === selectedGrade).map(p => p.subject))]
    : [];

  const filteredPapers = previousPapers.filter(paper => {
    if (!selectedGrade || !selectedSubject) return false;
    
    const matchesGrade = paper.grade === selectedGrade;
    const matchesSubject = paper.subject === selectedSubject;
    const matchesSearch = paper.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         paper.examType.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesYear = selectedYear === 'all' || paper.year === selectedYear;
    
    return matchesGrade && matchesSubject && matchesSearch && matchesYear;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link to="/student-dashboard" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Student Dashboard
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                Previous Year Papers
              </h1>
              <p className="text-gray-600 mt-1">Admin-uploaded exam papers for practice</p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Selection Flow */}
        {!selectedBranch || !selectedSemester || !selectedSubject ? (
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-center gap-4 mb-8 flex-wrap">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${selectedBranch ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                <span className="w-6 h-6 rounded-full bg-white flex items-center justify-center text-sm font-bold">1</span>
                <span className="font-medium">Select Branch</span>
              </div>
              <div className="w-8 h-0.5 bg-gray-300"></div>
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${selectedSemester ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                <span className="w-6 h-6 rounded-full bg-white flex items-center justify-center text-sm font-bold">2</span>
                <span className="font-medium">Select Semester</span>
              </div>
              <div className="w-8 h-0.5 bg-gray-300"></div>
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${selectedSubject ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                <span className="w-6 h-6 rounded-full bg-white flex items-center justify-center text-sm font-bold">3</span>
                <span className="font-medium">Select Subject</span>
              </div>
            </div>

            {/* Branch Selection */}
            {!selectedBranch && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl p-8 border border-gray-200 shadow-lg"
              >
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Select Your Branch</h2>
                  <p className="text-gray-600">Choose the branch to view available previous year papers</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {BRANCHES.map(branch => (
                    <button
                      key={branch}
                      onClick={() => setSelectedBranch(branch)}
                      className="p-6 rounded-xl border-2 border-gray-200 hover:border-purple-500 hover:bg-purple-50 transition-all text-center group"
                    >
                      <div className="text-sm font-bold text-gray-900 group-hover:text-purple-600 mb-2">
                        {branch}
                      </div>
                      <div className="text-xs text-gray-500">{SEMESTERS.length} semesters</div>
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
                className="bg-white rounded-2xl p-8 border border-gray-200 shadow-lg"
              >
                <button
                  onClick={() => {
                    setSelectedBranch('');
                    setSelectedSemester('');
                    setSelectedSubject('');
                  }}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium mb-6 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Change Branch
                </button>
                <div className="text-center mb-4">
                  <div className="inline-block px-4 py-2 bg-purple-100 text-purple-700 rounded-full font-bold">
                    {selectedBranch}
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 mt-4 mb-2">Select Semester</h2>
                  <p className="text-gray-600">Pick the semester you want to explore</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {SEMESTERS.map(semester => (
                    <button
                      key={semester}
                      onClick={() => setSelectedSemester(semester)}
                      className="p-6 rounded-xl border-2 border-gray-200 hover:border-purple-500 hover:bg-purple-50 transition-all text-center group"
                    >
                      <div className="text-sm font-bold text-gray-900 group-hover:text-purple-600 mb-2">
                        {semester}
                      </div>
                      <div className="text-xs text-gray-500">Select to see subjects</div>
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
                className="bg-white rounded-2xl p-8 border border-gray-200 shadow-lg"
              >
                <button
                  onClick={() => setSelectedSemester('')}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium mb-6 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Change Semester
                </button>
                <div className="text-center mb-8">
                  <div className="inline-block px-4 py-2 bg-purple-100 text-purple-700 rounded-full font-bold mb-3">
                    {selectedBranch} • {selectedSemester}
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Select Subject</h2>
                  <p className="text-gray-600">Choose the paper subject you'd like to review</p>
                </div>
                {availableSubjects.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {availableSubjects.map(subject => (
                      <button
                        key={subject}
                        onClick={() => setSelectedSubject(subject)}
                        className="p-6 rounded-xl border-2 border-gray-200 hover:border-purple-500 hover:bg-purple-50 transition-all text-left group"
                      >
                        <div className="flex items-center gap-3 mb-2">
                          <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                            <BookOpen className="w-5 h-5 text-purple-600" />
                          </div>
                          <div>
                            <div className="font-bold text-gray-900 group-hover:text-purple-600">
                              {subject}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 mt-6">
                    No subjects available yet for this branch and semester.
                  </div>
                )}
              </motion.div>
            )}
          </div>
        ) : (
          <>
            {/* Current Selection Banner */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 mb-8 text-white">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-white/20 flex items-center justify-center">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-sm text-white/80 mb-1">Viewing Papers for</div>
                    <div className="text-2xl font-bold">{selectedBranch} • {selectedSemester} • {selectedSubject}</div>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setSelectedBranch('');
                    setSelectedSemester('');
                    setSelectedSubject('');
                    setSearchTerm('');
                    setSelectedYear('all');
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all font-semibold"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Change Selection
                </button>
              </div>
            </div>

            {/* Info Banner */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 mb-8 border border-purple-100">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <BookOpen className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 mb-1">Official Exam Papers</h3>
                  <p className="text-gray-600 text-sm">
                    These papers have been uploaded by the admin and contain authentic previous year examination questions. 
                    Use them to understand exam patterns and practice effectively.
                  </p>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl p-6 mb-8 border border-gray-200">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="w-5 h-5 text-gray-600" />
                <h3 className="font-bold text-gray-900">Filter Papers</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by title or exam type..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all"
                  />
                </div>

                {/* Year Filter */}
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                  className="px-4 py-2.5 border border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all"
                >
                  <option value="all">All Years</option>
                  {years.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
                <span>Showing {filteredPapers.length} {filteredPapers.length === 1 ? 'paper' : 'papers'}</span>
                {(searchTerm || selectedYear !== 'all') && (
                  <button
                    onClick={() => {
                      setSearchTerm('');
                      setSelectedYear('all');
                    }}
                    className="text-purple-600 hover:text-purple-700 font-medium"
                  >
                    Clear Filters
                  </button>
                )}
              </div>
            </div>

            {/* Papers Grid */}
            {filteredPapers.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredPapers.map((paper, index) => (
                  <motion.div
                    key={paper.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="bg-white rounded-xl p-6 border border-gray-200 hover:border-purple-300 hover:shadow-lg transition-all"
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-purple-50 flex items-center justify-center">
                          <FileText className="w-6 h-6 text-purple-600" />
                        </div>
                        <div>
                          <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded">
                            {paper.grade}
                          </span>
                        </div>
                      </div>
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded">
                        {paper.year}
                      </span>
                    </div>

                    {/* Title and Subject */}
                    <h3 className="font-bold text-gray-900 mb-2 text-lg">{paper.title}</h3>
                    <p className="text-gray-600 text-sm mb-4">{paper.subject} • {paper.examType}</p>

                    {/* Details */}
                    <div className="space-y-2 mb-4 pb-4 border-b border-gray-100">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Total Marks:</span>
                        <span className="font-semibold text-gray-900">{paper.totalMarks}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Duration:</span>
                        <span className="font-semibold text-gray-900">{paper.duration}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Uploaded:</span>
                        <span className="font-semibold text-gray-900 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(paper.uploadDate).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg transition-all">
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                      <button className="px-4 py-2.5 border border-gray-200 hover:border-purple-300 hover:bg-purple-50 rounded-lg transition-all">
                        <Eye className="w-4 h-4 text-gray-600" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">No Papers Found</h3>
                <p className="text-gray-600 mb-4">No papers available for this selection</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default PreviousYearPapers;
