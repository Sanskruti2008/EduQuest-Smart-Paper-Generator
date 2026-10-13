import { useEffect, useState } from 'react';
import { BookOpen, ListTodo, LoaderCircle } from 'lucide-react';
import SectionHeader from './SectionHeader';
import { API_CONFIG } from '../../utils/constants';

type AssignedSubject = {
  subject_id: number;
  subject_name: string;
  subject_code: string;
  branch: string;
  semester: number | string;
};

type SubjectResponse = {
  success: boolean;
  subjects: AssignedSubject[];
  error?: string;
};

export default function AssignedTasksSection({
  onSectionSelect,
}: {
  onSectionSelect?: (section: string) => void;
}) {
  const [subjects, setSubjects] = useState<AssignedSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const token = sessionStorage.getItem('authToken');

    const loadAssignedSubjects = async () => {
      if (!token) {
        setError('Your faculty session has expired. Please sign in again.');
        setLoading(false);
        return;
      }
      try {
        const response = await fetch(
          `${API_CONFIG.BACKEND_URL}/api/paper-generation/subjects`,
          {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          },
        );
        const data = await response.json() as SubjectResponse;
        if (!response.ok || !data.success || !Array.isArray(data.subjects)) {
          throw new Error(data.error || 'Unable to load assigned subjects.');
        }
        setSubjects(data.subjects);
      } catch (loadError) {
        if (!controller.signal.aborted) {
          setError(loadError instanceof Error ? loadError.message : 'Unable to load assigned subjects.');
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };

    void loadAssignedSubjects();
    return () => controller.abort();
  }, []);

  return (
    <section id="assigned-tasks" className="px-4 pb-8 md:px-8">
      <SectionHeader
        title="Assigned Tasks"
        subtitle="Your assigned subjects and paper-generation responsibilities."
        icon={ListTodo}
      />

      {error && (
        <div role="alert" className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center gap-2 rounded-2xl border border-white/60 bg-white/70 px-6 py-12 text-sm text-slate-500 shadow-xl">
          <LoaderCircle className="h-4 w-4 animate-spin" />
          Loading your assigned subjects...
        </div>
      ) : subjects.length === 0 ? (
        error ? null : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 px-6 py-12 text-center shadow-xl">
            <BookOpen className="mx-auto h-9 w-9 text-slate-300" />
            <p className="mt-3 font-semibold text-slate-700">No subjects assigned yet</p>
            <p className="mt-1 text-sm text-slate-500">Contact your administrator to receive subject assignments.</p>
          </div>
        )
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {subjects.map(subject => (
            <article key={subject.subject_id} className="rounded-2xl border border-white/60 bg-white/70 p-5 shadow-xl backdrop-blur-xl">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
                  <BookOpen className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-slate-800">{subject.subject_name}</h3>
                  <p className="mt-1 text-xs font-medium text-slate-500">{subject.subject_code}</p>
                </div>
              </div>
              <p className="mt-4 text-sm text-slate-600">
                {subject.branch} · Semester {subject.semester}
              </p>
              <p className="mt-2 text-xs font-semibold text-amber-700">Paper Setter</p>
              <button
                type="button"
                onClick={() => onSectionSelect?.('paper-generation')}
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 px-3 py-2 text-xs font-semibold text-white shadow-sm transition hover:shadow-md"
              >
                <BookOpen className="h-3.5 w-3.5" />
                Generate paper
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
