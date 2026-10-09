import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect, lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { QuestionBankProvider } from './context/QuestionBankContext';
import { ThemeProvider } from './context/ThemeContext';
import Dashboard from './pages/Dashboard';
const FacultyDashboard = lazy(() => import('./pages/FacultyDashboard'));
import StudentDashboard from './pages/StudentDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ModeratorDashboard from './pages/ModeratorDashboard';
import ReviewExtracted from './pages/ReviewExtracted';
import QuestionBank from './pages/QuestionBank';
import StudentQuestionBank from './pages/StudentQuestionBank';
import StudentCurriculum from './pages/StudentCurriculum';
import PreviousYearPapers from './pages/PreviousYearPapers';
import SamplePaperGenerator from './pages/SamplePaperGenerator';
import QuestionPaperOCR from './pages/QuestionPaperOCR';
import SyllabusAnalyzer from './pages/SyllabusAnalyzer';
import CurriculumUpload from './pages/CurriculumUpload';
import { Chatbot } from './components/Chatbot';

function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

function AdminProtectedRoute({ children }: { children: ReactNode }) {
  const hasAdminSession =
    sessionStorage.getItem('adminAuthenticated') === 'true' &&
    Boolean(sessionStorage.getItem('adminToken'));

  return hasAdminSession ? children : <Navigate to="/" replace />;
}

function App() {
  return (
    <ThemeProvider>
      <QuestionBankProvider>
        <Router>
          <ScrollToTop />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route
              path="/admin-dashboard"
              element={
                <AdminProtectedRoute>
                  <AdminDashboard />
                </AdminProtectedRoute>
              }
            />
            <Route path="/moderator-dashboard" element={<ModeratorDashboard />} />
            <Route
              path="/faculty-dashboard"
              element={
                <Suspense
                  fallback={
                    <div className="min-h-screen flex items-center justify-center text-slate-600">
                      Loading Faculty Dashboard...
                    </div>
                  }
                >
                  <FacultyDashboard />
                </Suspense>
              }
            />
            <Route path="/student-dashboard" element={<StudentDashboard />} />
            <Route path="/faculty" element={<FacultyDashboard />} />
            <Route path="/question-bank" element={<QuestionBank />} />
            <Route path="/student-question-bank" element={<StudentQuestionBank />} />
            <Route path="/student-curriculum" element={<StudentCurriculum />} />
            <Route path="/syllabus-analyzer" element={<SyllabusAnalyzer />} />
            <Route path="/previous-year-papers" element={<PreviousYearPapers />} />
            <Route path="/sample-paper-generator" element={<SamplePaperGenerator />} />
            <Route path="/ocr-upload" element={<QuestionPaperOCR />} />
            <Route path="/curriculum-upload" element={<CurriculumUpload />} />
            <Route path="/review-extracted" element={<ReviewExtracted />} />
          </Routes>
          <Chatbot />
        </Router>
      </QuestionBankProvider>
    </ThemeProvider>
  );
}

export default App;
