export type FacultyProfile = {
  user_id: number;
  name: string | null;
  email: string | null;
  employee_id: string | null;
  department: string | null;
  role: string;
  is_active: boolean;
};

export type FacultyResponsibilities = {
  can_generate: boolean;
  can_moderate: boolean;
  generation_subject_count: number;
  moderation_subject_count: number;
};
