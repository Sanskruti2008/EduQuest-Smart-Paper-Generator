import { Link } from 'react-router-dom';
import { BookOpen, ArrowLeft, Search, Filter, TrendingUp, FileText, Calendar, GraduationCap } from 'lucide-react';

const StudentDashboard = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link to="/" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
            Student Dashboard
          </h1>
          <p className="text-gray-600 mt-2">Access your learning resources and question bank</p>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-2xl p-8 mb-12 border border-green-100">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Your Learning Hub! 📚</h2>
          <p className="text-gray-700 mb-6">
            Explore our comprehensive question bank to practice and prepare for your exams. 
            Filter by grade, subject, and difficulty level to find the perfect questions for your study session.
          </p>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200">
              <Search className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Search Questions</span>
            </div>
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200">
              <Filter className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Filter by Topic</span>
            </div>
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200">
              <TrendingUp className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">Track Progress</span>
            </div>
          </div>
        </div>

        {/* Main Action Card */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <Link to="/student-question-bank" className="no-underline">
            <div className="bg-white rounded-xl p-6 md:p-10 border-2 border-green-200 hover:border-green-300 hover:shadow-2xl transition-all duration-300 cursor-pointer group h-full">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-xl bg-green-50 flex items-center justify-center group-hover:bg-green-100 transition-colors">
                  <BookOpen className="w-9 h-9 text-green-600" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-gray-900 group-hover:text-gray-700 transition-colors">
                    Question Bank
                  </h3>
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-green-600 mt-1">
                    Browse & Practice
                  </span>
                </div>
              </div>
              <p className="text-gray-600 text-base leading-relaxed mb-6">
                Access thousands of practice questions organized by branch, semester, and subject. 
                Perfect for exam preparation and self-study.
              </p>
              <div className="flex items-center gap-3 text-sm text-gray-500 flex-wrap">
                <span className="bg-green-100 text-green-700 px-4 py-2 rounded-full font-medium">All Branches</span>
                <span className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full font-medium">All Subjects</span>
                <span className="bg-purple-100 text-purple-700 px-4 py-2 rounded-full font-medium">Give Feedback</span>
              </div>
            </div>
          </Link>

          <Link to="/student-curriculum" className="no-underline">
            <div className="bg-white rounded-xl p-10 border-2 border-blue-200 hover:border-blue-300 hover:shadow-2xl transition-all duration-300 cursor-pointer group h-full">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-xl bg-blue-50 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                  <GraduationCap className="w-9 h-9 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-gray-900 group-hover:text-gray-700 transition-colors">
                    Curriculum
                  </h3>
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 mt-1">
                    Branch-wise Syllabus
                  </span>
                </div>
              </div>
              <p className="text-gray-600 text-base leading-relaxed mb-6">
                View complete curriculum and subject-wise syllabus for all engineering branches. 
                Download PDFs and access detailed course content.
              </p>
              <div className="flex items-center gap-3 text-sm text-gray-500 flex-wrap">
                <span className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full font-medium">6 Branches</span>
                <span className="bg-purple-100 text-purple-700 px-4 py-2 rounded-full font-medium">All Semesters</span>
                <span className="bg-green-100 text-green-700 px-4 py-2 rounded-full font-medium">Download PDF</span>
              </div>
            </div>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <Link to="/previous-year-papers" className="no-underline">
            <div className="bg-white rounded-xl p-10 border-2 border-purple-200 hover:border-purple-300 hover:shadow-2xl transition-all duration-300 cursor-pointer group h-full">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-xl bg-purple-50 flex items-center justify-center group-hover:bg-purple-100 transition-colors">
                  <FileText className="w-9 h-9 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-gray-900 group-hover:text-gray-700 transition-colors">
                    Previous Year Papers
                  </h3>
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-purple-600 mt-1">
                    <Calendar className="w-3 h-3" />
                    Admin Uploaded
                  </span>
                </div>
              </div>
              <p className="text-gray-600 text-base leading-relaxed mb-6">
                Download and practice with authentic previous year examination papers uploaded by admin. 
                Understand exam patterns and improve your preparation.
              </p>
              <div className="flex items-center gap-3 text-sm text-gray-500 flex-wrap">
                <span className="bg-purple-100 text-purple-700 px-4 py-2 rounded-full font-medium">2020-2024</span>
                <span className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full font-medium">All Boards</span>
                <span className="bg-green-100 text-green-700 px-4 py-2 rounded-full font-medium">Download PDF</span>
              </div>
            </div>
          </Link>

          <Link to="/sample-paper-generator" className="no-underline">
            <div className="bg-white rounded-xl p-10 border-2 border-pink-200 hover:border-pink-300 hover:shadow-2xl transition-all duration-300 cursor-pointer group h-full">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-gray-900 group-hover:text-gray-700 transition-colors">
                    AI Paper Generator
                  </h3>
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-pink-600 mt-1">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    AI-Powered
                  </span>
                </div>
              </div>
              <p className="text-gray-600 text-base leading-relaxed mb-6">
                Generate custom practice papers instantly using AI. Matches MSBTE format, curriculum patterns, and difficulty distribution automatically.
              </p>
              <div className="flex items-center gap-3 text-sm text-gray-500 flex-wrap">
                <span className="bg-pink-100 text-pink-700 px-4 py-2 rounded-full font-medium">MSBTE Format</span>
                <span className="bg-purple-100 text-purple-700 px-4 py-2 rounded-full font-medium">Auto-Generate</span>
                <span className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full font-medium">Smart AI</span>
              </div>
            </div>
          </Link>
        </div>

        {/* Features Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h4 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                <Search className="w-4 h-4 text-blue-600" />
              </div>
              Smart Search
            </h4>
            <p className="text-gray-600 text-sm">
              Quickly find questions by keyword, topic, or chapter. Our intelligent search helps you locate exactly what you need.
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h4 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center">
                <Filter className="w-4 h-4 text-green-600" />
              </div>
              Advanced Filters
            </h4>
            <p className="text-gray-600 text-sm">
              Filter questions by grade, year, subject, chapter, and difficulty level to create your perfect practice set.
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h4 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center">
                <FileText className="w-4 h-4 text-purple-600" />
              </div>
              Previous Papers
            </h4>
            <p className="text-gray-600 text-sm">
              Access authentic previous year examination papers uploaded by admin to understand exam patterns.
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl p-6 border border-gray-200 text-center">
            <div className="text-4xl font-bold text-green-600 mb-2">1000+</div>
            <div className="text-gray-600 font-medium">Practice Questions</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200 text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">15+</div>
            <div className="text-gray-600 font-medium">Subject Areas</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200 text-center">
            <div className="text-4xl font-bold text-purple-600 mb-2">3</div>
            <div className="text-gray-600 font-medium">Difficulty Levels</div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center bg-gradient-to-r from-green-600 to-blue-600 rounded-2xl p-10 md:p-12 text-white">
          <h2 className="text-3xl md:text-4xl font-bold mb-3">Ready to Start Practicing?</h2>
          <p className="text-lg text-white/90 mb-6 max-w-2xl mx-auto">
            Access our comprehensive question bank and start preparing for your exams today!
          </p>
          <Link to="/question-bank">
            <button className="px-10 py-4 bg-white text-green-600 font-bold rounded-lg hover:bg-gray-100 transition-all shadow-lg text-lg">
              Browse Question Bank
            </button>
          </Link>
        </div>
      </main>
    </div>
  );
};

export default StudentDashboard;
