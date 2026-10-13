import { useEffect, useMemo, useState } from 'react';
import { API_CONFIG } from '../../utils/constants';

type FacultyOption = {
  user_id: number;
  name: string;
  is_active: boolean;
};

type SubjectOption = {
  subject_id: number;
  subject_name: string;
  subject_code?: string | null;
  branch?: string | null;
  semester?: string | null;
};

type Assignment = {
  subject_id: number;
  can_generate: boolean;
  can_moderate: boolean;
  is_active: boolean;
  subject: SubjectOption;
};

type ApiResponse = {
  success: boolean;
  message?: string;
  faculty?: FacultyOption[];
  subjects?: SubjectOption[];
  assignments?: Assignment[];
  assignment?: Assignment;
};

async function adminRequest(path: string, init: RequestInit = {}): Promise<ApiResponse> {
  const token = sessionStorage.getItem('adminToken');
  if (!token) throw new Error('Admin session expired. Please sign in again.');
  const response = await fetch(`${API_CONFIG.BACKEND_URL}${path}`, {
    ...init,
    headers: {
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  const data = await response.json() as ApiResponse;
  if (!response.ok || !data.success) {
    throw new Error(data.message || 'Unable to complete the assignment request.');
  }
  return data;
}

export default function AssignDuties() {
  const [faculty, setFaculty] = useState<FacultyOption[]>([]);
  const [subjects, setSubjects] = useState<SubjectOption[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [facultyId, setFacultyId] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [canGenerate, setCanGenerate] = useState(true);
  const [canModerate, setCanModerate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const selectedAssignment = useMemo(
    () => assignments.find(item => String(item.subject_id) === subjectId),
    [assignments, subjectId],
  );

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      adminRequest('/api/admin/faculty'),
      adminRequest('/api/admin/subjects'),
    ]).then(([facultyResponse, subjectResponse]) => {
      if (cancelled) return;
      setFaculty((facultyResponse.faculty || []).filter(item => item.is_active));
      setSubjects(subjectResponse.subjects || []);
    }).catch(loadError => {
      if (!cancelled) {
        setError(loadError instanceof Error ? loadError.message : 'Unable to load assignment options.');
      }
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setAssignments([]);
    setSubjectId('');
    if (!facultyId) return;
    adminRequest(`/api/admin/faculty/${facultyId}/assignments`)
      .then(response => {
        if (!cancelled) setAssignments(response.assignments || []);
      })
      .catch(loadError => {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Unable to load assignments.');
        }
      });
    return () => { cancelled = true; };
  }, [facultyId]);

  useEffect(() => {
    setCanGenerate(selectedAssignment?.can_generate ?? true);
    setCanModerate(selectedAssignment?.can_moderate ?? false);
  }, [selectedAssignment]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!facultyId || !subjectId) {
      setError('Select both a faculty member and a subject.');
      return;
    }
    if (!canGenerate && !canModerate) {
      setError('Select Paper Setter, Moderator, or both.');
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const response = await adminRequest(`/api/admin/faculty/${facultyId}/subjects`, {
        method: 'POST',
        body: JSON.stringify({
          subject_id: Number(subjectId),
          can_generate: canGenerate,
          can_moderate: canModerate,
        }),
      });
      setNotice(response.message || 'Responsibilities saved.');
      const refreshed = await adminRequest(`/api/admin/faculty/${facultyId}/assignments`);
      setAssignments(refreshed.assignments || []);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save responsibilities.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-6 px-4 py-8 md:px-8">
      <header>
        <h2 className="text-2xl font-bold text-slate-800">Assign Duties</h2>
        <p className="mt-1 text-sm text-slate-500">
          Set paper-generation and moderation responsibilities per subject. Account roles remain admin or faculty.
        </p>
      </header>

      {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {notice && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</p>}

      <form onSubmit={handleSubmit} className="max-w-3xl space-y-5 rounded-2xl border border-white/60 bg-white/80 p-6 shadow-sm">
        {loading ? <p className="text-sm text-slate-500">Loading faculty and subjects...</p> : (
          <>
            <label className="block text-sm font-semibold text-slate-700">
              Faculty
              <select value={facultyId} onChange={event => setFacultyId(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5">
                <option value="">Select faculty</option>
                {faculty.map(person => <option key={person.user_id} value={person.user_id}>{person.name}</option>)}
              </select>
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Subject
              <select value={subjectId} onChange={event => setSubjectId(event.target.value)} disabled={!facultyId} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 disabled:opacity-50">
                <option value="">Select subject</option>
                {subjects.map(subject => (
                  <option key={subject.subject_id} value={subject.subject_id}>
                    {subject.subject_name}{subject.subject_code ? ` (${subject.subject_code})` : ''}{subject.branch ? ` · ${subject.branch}` : ''}
                  </option>
                ))}
              </select>
            </label>
            <fieldset className="space-y-3">
              <legend className="text-sm font-semibold text-slate-700">Responsibilities</legend>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={canGenerate} onChange={event => setCanGenerate(event.target.checked)} />
                Paper Setter
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={canModerate} onChange={event => setCanModerate(event.target.checked)} />
                Moderator
              </label>
            </fieldset>
            <button type="submit" disabled={saving || loading || !facultyId || !subjectId} className="rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">
              {saving ? 'Saving...' : selectedAssignment ? 'Update Responsibility' : 'Assign Responsibility'}
            </button>
          </>
        )}
      </form>

      {facultyId && (
        <section className="max-w-3xl rounded-2xl border border-white/60 bg-white/80 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800">Current subject responsibilities</h3>
          {assignments.length === 0 ? <p className="mt-3 text-sm text-slate-500">No active assignments.</p> : (
            <ul className="mt-4 divide-y divide-slate-100">
              {assignments.filter(item => item.is_active).map(item => (
                <li key={item.subject_id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                  <span className="font-medium text-slate-800">{item.subject.subject_name}</span>
                  <span className="text-xs text-slate-600">
                    {[item.can_generate && 'Paper Setter', item.can_moderate && 'Moderator'].filter(Boolean).join(' + ')}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </section>
  );
}
