// API Configuration
export const API_CONFIG = {
  BACKEND_URL: 'http://localhost:5000',
  ENDPOINTS: {
    HEALTH: '/api/health'
  }
};

// Animation Delays
export const ANIMATION_DELAYS = {
  CARD_1: 0.1,
  CARD_2: 0.2,
  CARD_3: 0.3,
  BUTTON: 0.4
};

export const BRANCHES = [
  'Computer Technology',
  'Mechanical Engineering',
  'Civil Engineering',
  'Electrical Engineering',
  'Electronics Engineering'
];

export const SEMESTERS = [
  '1',
  '2',
  '3',
  '4',
  '5',
  '6'
];

const COMMON_FIRST_SEMESTER_SUBJECTS = [
  'Communication Skills (CMS)',
  'Applied Mathematics',
  'Applied Science',
  'Workshop Technology',
  'Engineering Drawing',
];

export const SUBJECT_CATALOG: Record<string, Record<string, string[]>> = {
  'Computer Technology': {
    '1': COMMON_FIRST_SEMESTER_SUBJECTS,
    '2': ['Basic Electronics', 'Digital Techniques', 'Programming in C', 'Applied Mathematics – II', 'Engineering Graphics'],
    '3': ['Data Structures using C', 'Digital Electronics', 'Computer Organization', 'Object Oriented Programming', 'Discrete Mathematics'],
    '4': ['Operating Systems', 'Database Management Systems', 'Computer Networks', 'Web Development', 'Software Engineering'],
    '5': ['Microprocessors & Interfaces', 'Advanced Java', 'Artificial Intelligence', 'Information Security', 'Industrial Organization and Management (IOM)', 'Elective – I'],
    '6': ['Mobile Application Development', 'Cloud Computing', 'Machine Learning', 'Project Work', 'Elective – II'],
  },
  'Mechanical Engineering': {
    '1': COMMON_FIRST_SEMESTER_SUBJECTS,
    '2': ['Applied Mathematics – II', 'Applied Mechanics', 'Material Science', 'Engineering Drawing – II', 'Basic Electronics'],
    '3': ['Engineering Mechanics', 'Strength of Materials', 'Thermodynamics', 'Manufacturing Processes – I', 'Metrology'],
    '4': ['Fluid Mechanics', 'Heat Transfer', 'Manufacturing Processes – II', 'Theory of Machines', 'Industrial Management'],
    '5': ['Machine Design', 'Refrigeration & Air Conditioning', 'CNC Technology', 'Power Plant Engineering', 'Elective – I'],
    '6': ['Mechatronics', 'Automobile Engineering', 'Project Work', 'Industrial Training', 'Elective – II'],
  },
  'Civil Engineering': {
    '1': COMMON_FIRST_SEMESTER_SUBJECTS,
    '2': ['Applied Mathematics – II', 'Applied Mechanics', 'Building Materials & Construction', 'Engineering Drawing – II', 'Basic Electronics'],
    '3': ['Surveying – I', 'Structural Mechanics', 'Concrete Technology', 'Hydraulics', 'Building Planning & Drawing'],
    '4': ['Surveying – II', 'Structural Analysis', 'Geotechnical Engineering', 'Irrigation Engineering', 'Environmental Engineering'],
    '5': ['Estimation & Costing', 'Reinforced Concrete Structures', 'Highway Engineering', 'Construction Management', 'Elective – I'],
    '6': ['Transportation Engineering', 'Advanced Construction Techniques', 'Computer Aided Design', 'Project Work', 'Elective – II'],
  },
  'Electrical Engineering': {
    '1': COMMON_FIRST_SEMESTER_SUBJECTS,
    '2': ['Applied Mathematics – II', 'Applied Science – II', 'Basic Electronics', 'Engineering Drawing', 'DC Circuits'],
    '3': ['Circuit Theory', 'Electrical Measurements', 'Digital Electronics', 'AC Circuits', 'Electronic Devices'],
    '4': ['Electrical Machines – I', 'Control Systems', 'Microprocessors', 'Power Electronics', 'Industrial Electronics'],
    '5': ['Electrical Machines – II', 'Power Systems – I', 'Programmable Logic Controllers', 'Electrical Estimation', 'Elective – I'],
    '6': ['Power Systems – II', 'Switchgear & Protection', 'Energy Management', 'Project Work', 'Elective – II'],
  },
  'Electronics Engineering': {
    '1': COMMON_FIRST_SEMESTER_SUBJECTS,
    '2': ['Applied Mathematics – II', 'Applied Science – II', 'DC Circuits', 'Engineering Drawing', 'Workshop Technology – II'],
    '3': ['Analog Electronics – I', 'Digital Electronics', 'Electronic Measurements', 'AC Circuits', 'Electronic Devices & Circuits'],
    '4': ['Analog Electronics – II', 'Communication Systems', 'Microprocessors & Applications', 'Linear Integrated Circuits', 'Power Electronics'],
    '5': ['Embedded Systems', 'VLSI Design', 'Signal Processing', 'Industrial Electronics', 'Elective – I'],
    '6': ['Advanced Communication Systems', 'IoT & Applications', 'Mobile Communication', 'Project Work', 'Elective – II'],
  },
};

export const formatBranchSemester = (branch: string, semester: string) => {
  if (!branch || !semester) return '';
  return `${branch} - Semester ${semester}`;
};

export const parseBranchSemesterLabel = (label: string) => {
  if (!label) return { branch: '', semester: '' };
  const parts = label.split(' - ');
  const branch = parts[0] ?? '';
  const semester = parts.slice(1).join(' - ') ?? '';
  return { branch: branch.trim(), semester: semester.trim() };
};

export const BRANCH_SEMESTER_OPTIONS = BRANCHES.flatMap(branch =>
  SEMESTERS.map(semester => formatBranchSemester(branch, semester))
);
