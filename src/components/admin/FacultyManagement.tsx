import { useEffect, useState } from 'react';
import {
  BookOpen,
  Check,
  LoaderCircle,
  Pencil,
  UserCheck,
  Users,
  UserX,
  X,
} from 'lucide-react';
import { API_CONFIG } from '../../utils/constants';

type FacultyRecord = {
  user_id: number;
  name: string;
  employee_id: string;
  email: string;
  department: string;
  role: 'faculty';
  is_active: boolean;
  assigned_subjects_count: number;
  assigned_subject_ids: number[];
  paper_setter_subjects_count: number;
  moderator_subjects_count: number;
};

type FacultySubject = {
  subject_id: number;
  subject_name: string;
  subject_code: string | null;
  branch: string | null;
  semester: string | null;
};

type FacultyForm = {
  name: string;
  employee_id: string;
  email: string;
  department: string;
  password: string;
  confirm_password: string;
  is_active: boolean;
};

type FacultyApiResponse = {
  success: boolean;
  message?: string;
  faculty?: FacultyRecord | FacultyRecord[];
  subjects?: FacultySubject[];
  errors?: Record<string, string>;
};

class FacultyRequestError extends Error {
  fieldErrors: Record<string, string>;

  constructor(message: string, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.fieldErrors = fieldErrors;
  }
}

async function facultyApiRequest(
  path: string,
  options: RequestInit = {},
): Promise<FacultyApiResponse> {
  const token = sessionStorage.getItem('adminToken');
  if (!token) {
    throw new FacultyRequestError('Admin session expired. Please sign in again.');
  }

  const response = await fetch(`${API_CONFIG.BACKEND_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
  let data: FacultyApiResponse;
  try {
    data = await response.json() as FacultyApiResponse;
  } catch {
    throw new FacultyRequestError('The server returned an invalid response.');
  }
  if (!data || typeof data.success !== 'boolean') {
    throw new FacultyRequestError('The server returned an invalid response.');
  }
  if (!response.ok || !data.success) {
    throw new FacultyRequestError(
      data.message || 'Unable to complete the request.',
      data.errors || {},
    );
  }
  return data;
}

const emptyFacultyForm = (): FacultyForm => ({
  name: '',
  employee_id: '',
  email: '',
  department: '',
  password: '',
  confirm_password: '',
  is_active: true,
});

export default function FacultyManagement() {
  const [facultyList, setFacultyList] = useState<FacultyRecord[]>([]);
  const [loadingFaculty, setLoadingFaculty] = useState(true);
  const [facultyError, setFacultyError] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState<FacultyRecord | null>(null);
  const [facultyForm, setFacultyForm] = useState<FacultyForm>(emptyFacultyForm);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [formMessage, setFormMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [updatingFacultyId, setUpdatingFacultyId] = useState<number | null>(null);
  const [assignmentFaculty, setAssignmentFaculty] = useState<FacultyRecord | null>(null);
  const [subjects, setSubjects] = useState<FacultySubject[]>([]);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [assigningSubjectId, setAssigningSubjectId] = useState<number | null>(null);

  const loadFaculty = async () => {
    setLoadingFaculty(true);
    setFacultyError(null);
    try {
      const data = await facultyApiRequest('/api/admin/faculty');
      setFacultyList(Array.isArray(data.faculty) ? data.faculty : []);
    } catch (error) {
      setFacultyError(error instanceof Error ? error.message : 'Unable to load faculty records.');
    } finally {
      setLoadingFaculty(false);
    }
  };

  useEffect(() => {
    void loadFaculty();
  }, []);

  useEffect(() => {
    if (!successNotice) return;
    const timeout = window.setTimeout(() => setSuccessNotice(null), 4000);
    return () => window.clearTimeout(timeout);
  }, [successNotice]);

  const openAddModal = () => {
    setEditingFaculty(null);
    setFacultyForm(emptyFacultyForm());
    setFormErrors({});
    setFormMessage(null);
    setIsModalOpen(true);
  };

  const openEditModal = (faculty: FacultyRecord) => {
    setEditingFaculty(faculty);
    setFacultyForm({
      ...emptyFacultyForm(),
      name: faculty.name,
      employee_id: faculty.employee_id,
      email: faculty.email,
      department: faculty.department,
      is_active: faculty.is_active,
    });
    setFormErrors({});
    setFormMessage(null);
    setIsModalOpen(true);
  };

  const closeForm = () => {
    if (isSaving) return;
    setIsModalOpen(false);
    setFormMessage(null);
    setFormErrors({});
  };

  const handleSaveFaculty = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const errors: Record<string, string> = {};
    if (!facultyForm.name.trim()) errors.name = 'Full name is required.';
    if (!facultyForm.employee_id.trim()) errors.employee_id = 'Employee ID is required.';
    if (!facultyForm.department.trim()) errors.department = 'Department is required.';
    if (!editingFaculty) {
      if (!facultyForm.email.trim()) errors.email = 'Email is required.';
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(facultyForm.email.trim())) {
        errors.email = 'Enter a valid email address.';
      }
      if (facultyForm.password.length < 8) errors.password = 'Use at least 8 characters.';
      if (facultyForm.password !== facultyForm.confirm_password) {
        errors.confirm_password = 'Passwords do not match.';
      }
    }
    setFormErrors(errors);
    setFormMessage(null);
    if (Object.keys(errors).length) return;

    setIsSaving(true);
    try {
      const path = editingFaculty
        ? `/api/admin/faculty/${editingFaculty.user_id}`
        : '/api/admin/faculty';
      const payload = editingFaculty
        ? {
            name: facultyForm.name.trim(),
            employee_id: facultyForm.employee_id.trim(),
            department: facultyForm.department.trim(),
          }
        : {
            name: facultyForm.name.trim(),
            employee_id: facultyForm.employee_id.trim(),
            email: facultyForm.email.trim(),
            department: facultyForm.department.trim(),
            password: facultyForm.password,
            is_active: facultyForm.is_active,
          };
      const data = await facultyApiRequest(path, {
        method: editingFaculty ? 'PATCH' : 'POST',
        body: JSON.stringify(payload),
      });
      if (data.faculty && !Array.isArray(data.faculty)) {
        const createdOrUpdatedFaculty = data.faculty;
        setFacultyList(current => {
          if (!editingFaculty) return [createdOrUpdatedFaculty, ...current];
          return current.map(faculty => faculty.user_id === createdOrUpdatedFaculty.user_id
            ? { ...faculty, ...createdOrUpdatedFaculty }
            : faculty);
        });
      }
      setIsModalOpen(false);
      setSuccessNotice(data.message || 'Faculty account saved successfully.');
      setFacultyError(null);
      void loadFaculty();
    } catch (error) {
      if (error instanceof FacultyRequestError) {
        setFormErrors(error.fieldErrors);
        setFormMessage(error.message);
      } else {
        setFormMessage('Unable to save faculty account. Please try again.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const toggleFacultyStatus = async (faculty: FacultyRecord) => {
    setUpdatingFacultyId(faculty.user_id);
    setFacultyError(null);
    try {
      const data = await facultyApiRequest(`/api/admin/faculty/${faculty.user_id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !faculty.is_active }),
      });
      if (data.faculty && !Array.isArray(data.faculty)) {
        const updatedFaculty = data.faculty;
        setFacultyList(current => current.map(item => item.user_id === faculty.user_id
          ? { ...item, ...updatedFaculty }
          : item));
      }
      setSuccessNotice(faculty.is_active ? 'Faculty account deactivated.' : 'Faculty account activated.');
      void loadFaculty();
    } catch (error) {
      setFacultyError(error instanceof Error ? error.message : 'Unable to update account status.');
    } finally {
      setUpdatingFacultyId(null);
    }
  };

  const openAssignmentModal = async (faculty: FacultyRecord) => {
    setAssignmentFaculty(faculty);
    setAssignmentError(null);
    setLoadingSubjects(true);
    try {
      const data = await facultyApiRequest('/api/admin/subjects');
      setSubjects(data.subjects || []);
    } catch (error) {
      setAssignmentError(error instanceof Error ? error.message : 'Unable to load subjects.');
    } finally {
      setLoadingSubjects(false);
    }
  };

  const assignSubject = async (subjectId: number) => {
    if (!assignmentFaculty) return;
    setAssigningSubjectId(subjectId);
    setAssignmentError(null);
    try {
      await facultyApiRequest(
        `/api/admin/faculty/${assignmentFaculty.user_id}/subjects`,
        { method: 'POST', body: JSON.stringify({ subject_id: subjectId }) },
      );
      setFacultyList(current => current.map(faculty => {
        if (faculty.user_id !== assignmentFaculty.user_id
          || faculty.assigned_subject_ids.includes(subjectId)) return faculty;
        const assignedSubjectIds = [...faculty.assigned_subject_ids, subjectId];
        return {
          ...faculty,
          assigned_subject_ids: assignedSubjectIds,
          assigned_subjects_count: assignedSubjectIds.length,
        };
      }));
      setAssignmentFaculty(current => current
        ? {
            ...current,
            assigned_subject_ids: current.assigned_subject_ids.includes(subjectId)
              ? current.assigned_subject_ids
              : [...current.assigned_subject_ids, subjectId],
          }
        : current);
      setSuccessNotice('Subject assigned successfully.');
      void loadFaculty();
    } catch (error) {
      setAssignmentError(error instanceof Error ? error.message : 'Unable to assign subject.');
    } finally {
      setAssigningSubjectId(null);
    }
  };

  const inputClass = (field: string) =>
    `mt-1 w-full rounded-xl border bg-slate-50 px-3 py-2.5 text-sm text-slate-800 outline-none transition focus:ring-2 focus:ring-amber-400 ${
      formErrors[field] ? 'border-rose-400' : 'border-slate-200'
    }`;

  const renderFieldError = (field: string) => formErrors[field] && (
    <p className="mt-1 text-xs text-rose-600">{formErrors[field]}</p>
  );

  return (
    <section className="relative space-y-6 px-4 py-8 md:px-8">
      {successNotice && (
        <div role="status" className="fixed right-5 top-5 z-[70] flex items-center gap-2 rounded-xl border border-emerald-200 bg-white px-4 py-3 text-sm font-medium text-emerald-700 shadow-lg">
          <Check className="h-4 w-4" />
          {successNotice}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Faculty Management</h2>
          <p className="mt-1 text-sm text-slate-500">Manage faculty accounts and subject responsibilities.</p>
        </div>
        <button
          onClick={openAddModal}
          className="rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md transition hover:shadow-lg"
        >
          + Add Faculty
        </button>
      </div>

      {facultyError && (
        <div role="alert" className="flex items-center justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <span>{facultyError}</span>
          <button onClick={() => void loadFaculty()} className="font-semibold underline">Retry</button>
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-white/60 bg-white/80 shadow-sm backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50/70 text-slate-500">
              <tr>
                <th className="px-5 py-4 font-medium">Faculty Name</th>
                <th className="px-5 py-4 font-medium">Employee ID</th>
                <th className="px-5 py-4 font-medium">Email</th>
                <th className="px-5 py-4 font-medium">Department</th>
                <th className="px-5 py-4 font-medium">Account Status</th>
                <th className="px-5 py-4 font-medium">Responsibilities</th>
                <th className="px-5 py-4 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loadingFaculty ? (
                <tr><td colSpan={7} className="px-6 py-10 text-center text-slate-500">Loading faculty accounts...</td></tr>
              ) : facultyList.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <Users className="mx-auto h-9 w-9 text-slate-300" />
                    <p className="mt-3 font-semibold text-slate-700">No faculty accounts yet</p>
                    <p className="mt-1 text-sm text-slate-500">Add a faculty member to get started.</p>
                  </td>
                </tr>
              ) : facultyList.map(faculty => (
                <tr key={faculty.user_id} className="transition hover:bg-slate-50/60">
                  <td className="px-5 py-4 font-semibold text-slate-800">{faculty.name}</td>
                  <td className="px-5 py-4 text-slate-600">{faculty.employee_id}</td>
                  <td className="px-5 py-4 text-slate-600">{faculty.email}</td>
                  <td className="px-5 py-4 text-slate-600">{faculty.department}</td>
                  <td className="px-5 py-4">
                    <span className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-semibold ${
                      faculty.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'
                    }`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${faculty.is_active ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                      {faculty.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-600">
                    <span className="block">{faculty.paper_setter_subjects_count} Paper Setter</span>
                    <span className="mt-1 block text-xs">{faculty.moderator_subjects_count} Moderator</span>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => openEditModal(faculty)} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
                        <Pencil className="h-3.5 w-3.5" /> View/Edit
                      </button>
                      <button
                        onClick={() => void openAssignmentModal(faculty)}
                        disabled={!faculty.is_active}
                        className="inline-flex items-center gap-1 rounded-lg border border-amber-200 px-2.5 py-1.5 text-xs font-semibold text-amber-700 transition hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <BookOpen className="h-3.5 w-3.5" /> Assign Subject
                      </button>
                      <button
                        onClick={() => void toggleFacultyStatus(faculty)}
                        disabled={updatingFacultyId === faculty.user_id}
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                      >
                        {updatingFacultyId === faculty.user_id ? (
                          <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                        ) : faculty.is_active ? (
                          <UserX className="h-3.5 w-3.5" />
                        ) : (
                          <UserCheck className="h-3.5 w-3.5" />
                        )}
                        {faculty.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-4">
          <button aria-label="Close modal" className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={closeForm} />
          <div role="dialog" aria-modal="true" aria-labelledby="faculty-modal-title" className="relative my-auto w-full max-w-xl rounded-3xl border border-white/60 bg-white p-6 shadow-2xl">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <h3 id="faculty-modal-title" className="text-xl font-bold text-slate-800">
                  {editingFaculty ? 'Edit Faculty' : 'Add Faculty'}
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  {editingFaculty ? 'Update faculty profile details.' : 'Create a secure faculty sign-in account.'}
                </p>
              </div>
              <button aria-label="Close modal" onClick={closeForm} className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSaveFaculty} className="space-y-4">
              {formMessage && (
                <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700">{formMessage}</div>
              )}
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-semibold text-slate-700">
                  Full Name *
                  <input autoComplete="name" value={facultyForm.name} onChange={event => setFacultyForm({ ...facultyForm, name: event.target.value })} className={inputClass('name')} />
                  {renderFieldError('name')}
                </label>
                <label className="block text-sm font-semibold text-slate-700">
                  Employee ID *
                  <input autoComplete="off" value={facultyForm.employee_id} onChange={event => setFacultyForm({ ...facultyForm, employee_id: event.target.value })} className={inputClass('employee_id')} />
                  {renderFieldError('employee_id')}
                </label>
                <label className="block text-sm font-semibold text-slate-700 sm:col-span-2">
                  Email *
                  <input type="email" autoComplete="email" value={facultyForm.email} disabled={!!editingFaculty} onChange={event => setFacultyForm({ ...facultyForm, email: event.target.value })} className={`${inputClass('email')} disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500`} />
                  {renderFieldError('email')}
                </label>
                <label className="block text-sm font-semibold text-slate-700 sm:col-span-2">
                  Department *
                  <input autoComplete="organization-title" value={facultyForm.department} onChange={event => setFacultyForm({ ...facultyForm, department: event.target.value })} className={inputClass('department')} />
                  {renderFieldError('department')}
                </label>
                {!editingFaculty && (
                  <>
                    <label className="block text-sm font-semibold text-slate-700">
                      Temporary Password *
                      <input type="password" autoComplete="new-password" value={facultyForm.password} onChange={event => setFacultyForm({ ...facultyForm, password: event.target.value })} className={inputClass('password')} />
                      {renderFieldError('password')}
                    </label>
                    <label className="block text-sm font-semibold text-slate-700">
                      Confirm Password *
                      <input type="password" autoComplete="new-password" value={facultyForm.confirm_password} onChange={event => setFacultyForm({ ...facultyForm, confirm_password: event.target.value })} className={inputClass('confirm_password')} />
                      {renderFieldError('confirm_password')}
                    </label>
                    <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 sm:col-span-2">
                      <input type="checkbox" checked={facultyForm.is_active} onChange={event => setFacultyForm({ ...facultyForm, is_active: event.target.checked })} className="h-4 w-4 rounded border-slate-300 text-amber-600 focus:ring-amber-500" />
                      Account active
                    </label>
                  </>
                )}
              </div>
              <div className="flex justify-end gap-3 border-t border-slate-100 pt-4">
                <button type="button" onClick={closeForm} disabled={isSaving} className="rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 disabled:opacity-50">
                  Cancel
                </button>
                <button type="submit" disabled={isSaving} className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md transition hover:shadow-lg disabled:cursor-wait disabled:opacity-70">
                  {isSaving && <LoaderCircle className="h-4 w-4 animate-spin" />}
                  {isSaving ? (editingFaculty ? 'Saving changes...' : 'Creating account...') : editingFaculty ? 'Save Changes' : 'Create Faculty Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {assignmentFaculty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-4">
          <button aria-label="Close assignment modal" className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setAssignmentFaculty(null)} />
          <div role="dialog" aria-modal="true" aria-labelledby="assignment-modal-title" className="relative my-auto w-full max-w-lg rounded-3xl border border-white/60 bg-white p-6 shadow-2xl">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <h3 id="assignment-modal-title" className="text-xl font-bold text-slate-800">Assign Subject</h3>
                <p className="mt-1 text-sm text-slate-500">{assignmentFaculty.name}</p>
              </div>
              <button aria-label="Close assignment modal" onClick={() => setAssignmentFaculty(null)} className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700">
                <X className="h-5 w-5" />
              </button>
            </div>
            {assignmentError && <div role="alert" className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700">{assignmentError}</div>}
            <div className="max-h-[55vh] space-y-2 overflow-y-auto">
              {loadingSubjects ? (
                <p className="py-8 text-center text-sm text-slate-500">Loading subjects...</p>
              ) : subjects.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-500">No subjects are available yet.</p>
              ) : subjects.map(subject => {
                const isAssigned = assignmentFaculty.assigned_subject_ids.includes(subject.subject_id);
                return (
                  <div key={subject.subject_id} className="flex items-center justify-between gap-4 rounded-xl border border-slate-100 px-4 py-3">
                    <div>
                      <p className="font-semibold text-slate-800">{subject.subject_name}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {[subject.subject_code, subject.branch, subject.semester ? `Semester ${subject.semester}` : null].filter(Boolean).join(' · ') || 'Subject'}
                      </p>
                    </div>
                    <button
                      disabled={isAssigned || assigningSubjectId !== null}
                      onClick={() => void assignSubject(subject.subject_id)}
                      className="shrink-0 rounded-lg border border-amber-200 px-3 py-1.5 text-xs font-semibold text-amber-700 transition hover:bg-amber-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                    >
                      {assigningSubjectId === subject.subject_id ? 'Assigning...' : isAssigned ? 'Assigned' : 'Assign'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
