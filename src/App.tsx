import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect, lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { QuestionBankProvider } from './context/QuestionBankContext';
import { ThemeProvider } from './context/ThemeContext';
import Dashboard from './pages/Dashboard';
const FacultyDashboard = lazy(() => import('./pages/FacultyDashboard'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const ModeratorDashboard = lazy(() => import('./pages/ModeratorDashboard'));
const ReviewExtracted = lazy(() => import('./pages/ReviewExtracted'));
const QuestionBank = lazy(() => import('./pages/QuestionBank'));
const StudentDashboard = lazy(() => import('./pages/StudentDashboard'));
const StudentQuestionBank = lazy(() => import('./pages/StudentQuestionBank'));
const StudentCurriculum = lazy(() => import('./pages/StudentCurriculum'));
const PreviousYearPapers = lazy(() => import('./pages/PreviousYearPapers'));
const SamplePaperGenerator = lazy(() => import('./pages/SamplePaperGenerator'));
const QuestionPaperOCR = lazy(() => import('./pages/QuestionPaperOCR'));
const SyllabusAnalyzer = lazy(() => import('./pages/SyllabusAnalyzer'));
const CurriculumUpload = lazy(() => import('./pages/CurriculumUpload'));
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

function PageLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center text-slate-600">
      Loading dashboard...
    </div>
  );
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
                <Suspense fallback={<PageLoading />}>
                  <AdminProtectedRoute>
                    <AdminDashboard />
                  </AdminProtectedRoute>
                </Suspense>
              }
            />
            <Route path="/moderator-dashboard" element={<Suspense fallback={<PageLoading />}><ModeratorDashboard /></Suspense>} />
            <Route path="/faculty-dashboard" element={<Suspense fallback={<PageLoading />}><FacultyDashboard /></Suspense>} />
            <Route path="/student-dashboard" element={<Suspense fallback={<PageLoading />}><StudentDashboard /></Suspense>} />
            <Route path="/faculty" element={<Suspense fallback={<PageLoading />}><FacultyDashboard /></Suspense>} />
            <Route path="/question-bank" element={<Suspense fallback={<PageLoading />}><QuestionBank /></Suspense>} />
            <Route path="/student-question-bank" element={<Suspense fallback={<PageLoading />}><StudentQuestionBank /></Suspense>} />
            <Route path="/student-curriculum" element={<Suspense fallback={<PageLoading />}><StudentCurriculum /></Suspense>} />
            <Route path="/syllabus-analyzer" element={<Suspense fallback={<PageLoading />}><SyllabusAnalyzer /></Suspense>} />
            <Route path="/previous-year-papers" element={<Suspense fallback={<PageLoading />}><PreviousYearPapers /></Suspense>} />
            <Route path="/sample-paper-generator" element={<Suspense fallback={<PageLoading />}><SamplePaperGenerator /></Suspense>} />
            <Route path="/ocr-upload" element={<Suspense fallback={<PageLoading />}><QuestionPaperOCR /></Suspense>} />
            <Route path="/curriculum-upload" element={<Suspense fallback={<PageLoading />}><CurriculumUpload /></Suspense>} />
            <Route path="/review-extracted" element={<Suspense fallback={<PageLoading />}><ReviewExtracted /></Suspense>} />
          </Routes>
          <Chatbot />
        </Router>
      </QuestionBankProvider>
    </ThemeProvider>
  );
}

export default App;
