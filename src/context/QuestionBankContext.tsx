import { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { API_CONFIG, formatBranchSemester } from '../utils/constants';

export interface Question {
  id: number;
  canonical_id?: string | number;
  text: string;
  chapter: string;
  subject: string;
  grade: string;
  year: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  marks: number;
  type: string;
  tags?: string[];
  image?: string;
  sub_label?: string;
  sub_questions?: Array<{ label: string; text: string; marks?: number }>;
  createdAt: string;
  updatedAt?: string;
}

export interface Feedback {
  id: number;
  questionId: number;
  questionText: string;
  subject: string;
  type: 'positive' | 'negative' | 'suggestion';
  message: string;
  createdAt: string;
  isRead: boolean;
}

interface QuestionBankContextType {
  questions: Question[];
  loading: boolean;
  error: string | null;
  fetchDbQuestions: (branch?: string | null, semester?: string | null, subject?: string | null, subjectId?: number | string | null) => Promise<void>;
  addQuestion: (question: Omit<Question, 'id' | 'createdAt'>) => void;
  updateQuestion: (id: number, question: Partial<Question>) => void;
  deleteQuestion: (id: number) => void;
  // Feedback functions
  feedbacks: Feedback[];
  addFeedback: (feedback: Omit<Feedback, 'id' | 'isRead'>) => void;
  markFeedbackAsRead: (id: number) => void;
  deleteFeedback: (id: number) => void;
  getUnreadFeedbackCount: () => number;
}

const QuestionBankContext = createContext<QuestionBankContextType | undefined>(undefined);

export const useQuestionBank = () => {
  const context = useContext(QuestionBankContext);
  if (!context) {
    throw new Error('useQuestionBank must be used within a QuestionBankProvider');
  }
  return context;
};

interface QuestionBankProviderProps {
  children: ReactNode;
}

export const QuestionBankProvider = ({ children }: QuestionBankProviderProps) => {
  const [questions, setQuestions] = useState<Question[]>(() => {
    const savedQuestions = localStorage.getItem('eduquest-question-bank');
    if (!savedQuestions) return [];

    try {
      const parsedQuestions = JSON.parse(savedQuestions);
      return Array.isArray(parsedQuestions) ? parsedQuestions : [];
    } catch (error) {
      console.error('Error loading saved questions:', error);
      localStorage.removeItem('eduquest-question-bank');
      return [];
    }
  });
  const [error, setError] = useState<string | null>(null);

  // Feedback state
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load feedbacks
    const savedFeedbacks = localStorage.getItem('eduquest-feedbacks');
    if (savedFeedbacks) {
      try {
        const parsedFeedbacks = JSON.parse(savedFeedbacks);
        if (parsedFeedbacks && parsedFeedbacks.length > 0) {
          setFeedbacks(parsedFeedbacks);
        }
      } catch (error) {
        console.error('Error loading feedbacks:', error);
      }
    }
  }, []);

  // Auto-save manually added and edited questions.
  useEffect(() => {
    localStorage.setItem('eduquest-question-bank', JSON.stringify(questions));
  }, [questions]);

  // Auto-save feedbacks to localStorage
  useEffect(() => {
    localStorage.setItem('eduquest-feedbacks', JSON.stringify(feedbacks));
  }, [feedbacks]);

  const addQuestion = (question: Omit<Question, 'id' | 'createdAt'>) => {
    const newQuestion: Question = {
      ...question,
      id: -Date.now(),
      createdAt: new Date().toISOString(),
    };
    setQuestions(prev => [...prev, newQuestion]);
  };

  const updateQuestion = (id: number, updates: Partial<Question>) => {
    setQuestions(prev =>
      prev.map(q =>
        q.id === id
          ? { ...q, ...updates, updatedAt: new Date().toISOString() }
          : q
      )
    );
  };

  const deleteQuestion = (id: number) => {
    setQuestions(prev => prev.filter(q => q.id !== id));
  };

  /**
   * Fetch questions from the backend DB (Supabase) and merge them into the
   * local question list. Already-existing local (user-added) questions are
   * preserved. DB questions are de-duplicated by id.
   */
  const fetchDbQuestions = async (
    branch?: string | null,
    semester?: string | null,
    subject?: string | null,
    subjectId?: number | string | null,
  ): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: '300' });
      if (branch)   params.set('branch',   branch);
      if (semester) params.set('semester', semester);
      if (subjectId !== null && subjectId !== undefined) {
        params.set('subject_id', String(subjectId));
      } else if (subject) {
        params.set('subject', subject);
      }

      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 8000);
      const resp = await fetch(`${API_CONFIG.BACKEND_URL}/api/questions?${params}`, {
        signal: controller.signal,
      });
      window.clearTimeout(timeout);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      if (!data.success || !Array.isArray(data.questions)) {
        throw new Error(data.error || 'The question bank response was invalid.');
      }

      const fullGrade = branch && semester ? formatBranchSemester(branch, semester) : '';

      const mapped: Question[] = data.questions.map((q: Record<string, any>) => {
        const paperBranch   = q.paper?.branch   || branch   || '';
        // Normalise semester: DB stores '1', '2' etc.; strip any ordinal suffix just in case
        const rawSem = (q.paper?.semester || q.grade || semester || '').toString().replace(/[^0-9]/g, '');
        const paperSemester = rawSem || semester || '';
        const grade = paperBranch && paperSemester
          ? formatBranchSemester(paperBranch, paperSemester)
          : fullGrade;
        const rawYear =
          q.paper?.exam_info?.exam_year?.toString()
          ?? (q.created_at ? String(q.created_at).split('-')[0] : String(new Date().getFullYear()));
        return {
          id         : Number(q.id ?? q.question_id),
          canonical_id: q.canonical_id,
          text       : String(q.text || q.question_text || ''),
          chapter    : String(q.chapter || 'General'),
          subject    : String(q.subject || subject || 'Unknown'),
          grade,
          year       : rawYear,
          difficulty : (q.difficulty || 'Medium') as 'Easy' | 'Medium' | 'Hard',
          marks      : Number(q.marks) || 4,
          type       : String(q.type || 'Short Answer'),
          tags       : q.bloom_level ? [String(q.bloom_level)] : [],
          sub_label  : q.sub_label ? String(q.sub_label) : undefined,
          sub_questions: Array.isArray(q.sub_questions) && q.sub_questions.length > 0
            ? q.sub_questions
            : undefined,
          createdAt  : String(q.created_at || new Date().toISOString()),
        };
      }).filter((q: Question) => q.text.trim().length > 0);

      // Keep manual questions for the selected context alongside database rows.
      setQuestions(previous => {
        const manualQuestions = previous.filter(question =>
          question.id < 0
          && question.grade === fullGrade
          && (!subject || question.subject === subject)
        );
        return [...mapped, ...manualQuestions];
      });
    } catch (err) {
      const message = err instanceof Error
        ? err.name === 'AbortError'
          ? 'The question bank took too long to respond. Please try again.'
          : err.message
        : 'Unable to load the question bank.';
      console.error('[QuestionBank] Failed to load from database:', err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // Feedback functions
  const addFeedback = (feedback: Omit<Feedback, 'id' | 'isRead'>) => {
    const newFeedback: Feedback = {
      ...feedback,
      id: Date.now(),
      isRead: false,
    };
    setFeedbacks(prev => [...prev, newFeedback]);
  };

  const markFeedbackAsRead = (id: number) => {
    setFeedbacks(prev =>
      prev.map(f =>
        f.id === id ? { ...f, isRead: true } : f
      )
    );
  };

  const deleteFeedback = (id: number) => {
    setFeedbacks(prev => prev.filter(f => f.id !== id));
  };

  const getUnreadFeedbackCount = () => {
    return feedbacks.filter(f => !f.isRead).length;
  };

  const value = {
    questions,
    loading,
    fetchDbQuestions,
    addQuestion,
    updateQuestion,
    deleteQuestion,
    // Feedback
    feedbacks,
    addFeedback,
    markFeedbackAsRead,
    deleteFeedback,
    getUnreadFeedbackCount,
  };

  return (
    <QuestionBankContext.Provider value={value}>
      {children}
    </QuestionBankContext.Provider>
  );
};
