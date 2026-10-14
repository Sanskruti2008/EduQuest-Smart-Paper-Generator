import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_CONFIG } from '../utils/constants';
import { saveReviewData } from '../utils/reviewData';
import { Download, FileText, Calendar, Users } from 'lucide-react';

interface UploadResult {
  success: boolean;
  message?: string;
  filename?: string;
  json_file?: string;
  questions_extracted?: boolean;
  extraction_source?: string;
  extracted_data?: {
    total_papers: number;
    exam_info?: any;
    papers: Array<{
      paper_number: number;
      paper_name?: string;
      questions: Array<{
        question_number: string;
        question_text: string;
        marks: number;
        course_outcome?: string;
        bloom_level?: string;
        has_math?: boolean;
      }>;
    }>;
  };
  database_result?: number | null;
  similarity?: {
    status: 'completed' | 'failed' | 'skipped';
    processed?: number;
    duplicates?: number;
    new_questions?: number;
    error?: string;
  } | null;
  error?: string;
}

interface UploadedPaper {
  paper_id: number;
  filename: string;
  subject: string;
  subject_code: string;
  branch: string;
  semester: string;
  exam_type: string;
  exam_year?: number;
  exam_date?: string;
  upload_date?: string;
  total_questions?: number;
}

// Branch and subject configuration (subjects keyed by semester)
const SEM1_COMMON = [
  'Communication Skills (CMS)',
  'Applied Mathematics',
  'Applied Science',
  'Workshop Technology',
  'Engineering Drawing',
];

const BRANCH_CONFIG = {
  'Computer Technology': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Basic Electronics', 'Digital Techniques', 'Programming in C', 'Applied Mathematics â€“ II', 'Engineering Graphics'],
      '3': ['Data Structures using C', 'Digital Electronics', 'Computer Organization', 'Object Oriented Programming', 'Discrete Mathematics'],
      '4': ['Operating Systems', 'Database Management Systems', 'Computer Networks', 'Web Development', 'Software Engineering'],
      '5': ['Microprocessors & Interfaces', 'Advanced Java', 'Artificial Intelligence', 'Information Security', 'Industrial Organization and Management (IOM)', 'PHP', 'Elective â€“ I'],
      '6': ['Mobile Application Development', 'Cloud Computing', 'Machine Learning', 'Project Work', 'Elective â€“ II'],
    },
  },
  'Mechanical Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Applied Mathematics â€“ II', 'Applied Mechanics', 'Material Science', 'Engineering Drawing â€“ II', 'Basic Electronics'],
      '3': ['Engineering Mechanics', 'Strength of Materials', 'Thermodynamics', 'Manufacturing Processes â€“ I', 'Metrology'],
      '4': ['Fluid Mechanics', 'Heat Transfer', 'Manufacturing Processes â€“ II', 'Theory of Machines', 'Industrial Management'],
      '5': ['Machine Design', 'Refrigeration & Air Conditioning', 'CNC Technology', 'Power Plant Engineering', 'Elective â€“ I'],
      '6': ['Mechatronics', 'Automobile Engineering', 'Project Work', 'Industrial Training', 'Elective â€“ II'],
    },
  },
  'Civil Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Applied Mathematics â€“ II', 'Applied Mechanics', 'Building Materials & Construction', 'Engineering Drawing â€“ II', 'Basic Electronics'],
      '3': ['Surveying â€“ I', 'Structural Mechanics', 'Concrete Technology', 'Hydraulics', 'Building Planning & Drawing'],
      '4': ['Surveying â€“ II', 'Structural Analysis', 'Geotechnical Engineering', 'Irrigation Engineering', 'Environmental Engineering'],
      '5': ['Estimation & Costing', 'Reinforced Concrete Structures', 'Highway Engineering', 'Construction Management', 'Elective â€“ I'],
      '6': ['Transportation Engineering', 'Advanced Construction Techniques', 'Computer Aided Design', 'Project Work', 'Elective â€“ II'],
    },
  },
  'Electrical Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Applied Mathematics â€“ II', 'Applied Science â€“ II', 'Basic Electronics', 'Engineering Drawing', 'DC Circuits'],
      '3': ['Circuit Theory', 'Electrical Measurements', 'Digital Electronics', 'AC Circuits', 'Electronic Devices'],
      '4': ['Electrical Machines â€“ I', 'Control Systems', 'Microprocessors', 'Power Electronics', 'Industrial Electronics'],
      '5': ['Electrical Machines â€“ II', 'Power Systems â€“ I', 'Programmable Logic Controllers', 'Electrical Estimation', 'Elective â€“ I'],
      '6': ['Power Systems â€“ II', 'Switchgear & Protection', 'Energy Management', 'Project Work', 'Elective â€“ II'],
    },
  },
  'Electronics Engineering': {
    semesters: ['1', '2', '3', '4', '5', '6'],
    subjects: {
      '1': SEM1_COMMON,
      '2': ['Applied Mathematics â€“ II', 'Applied Science â€“ II', 'DC Circuits', 'Engineering Drawing', 'Workshop Technology â€“ II'],
      '3': ['Analog Electronics â€“ I', 'Digital Electronics', 'Electronic Measurements', 'AC Circuits', 'Electronic Devices & Circuits'],
      '4': ['Analog Electronics â€“ II', 'Communication Systems', 'Microprocessors & Applications', 'Linear Integrated Circuits', 'Power Electronics'],
      '5': ['Embedded Systems', 'VLSI Design', 'Signal Processing', 'Industrial Electronics', 'Elective â€“ I'],
      '6': ['Advanced Communication Systems', 'IoT & Applications', 'Mobile Communication', 'Project Work', 'Elective â€“ II'],
    },
  },
};

const QuestionPaperUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [branch, setBranch] = useState('');
  const [semester, setSemester] = useState('');
  const [subject, setSubject] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [editableData, setEditableData] = useState<any>(null);
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();
  const [recentPapers, setRecentPapers] = useState<UploadedPaper[]>([]);
  const [loadingPapers, setLoadingPapers] = useState(false);

  // Fetch recently uploaded papers on component mount
  useEffect(() => {
    fetchRecentPapers();
  }, []);

  // Refresh papers list after successful upload
  useEffect(() => {
    if (result?.success) {
      const timer = setTimeout(fetchRecentPapers, 1000);
      return () => clearTimeout(timer);
    }
  }, [result?.success]);

  const fetchRecentPapers = async () => {
    setLoadingPapers(true);
    try {
      const token = sessionStorage.getItem('adminToken') || sessionStorage.getItem('authToken');
      if (!token) return;

      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/uploaded-papers?limit=5`, {
        headers: { Authorization: 'Bearer ' + token },
      });

      if (response.ok) {
        const data = await response.json();
        setRecentPapers(data.papers || []);
      }
    } catch (error) {
      console.error('Failed to fetch recent papers:', error);
    } finally {
      setLoadingPapers(false);
    }
  };
  
  // Get available semesters based on selected branch
  const availableSemesters = branch ? BRANCH_CONFIG[branch as keyof typeof BRANCH_CONFIG]?.semesters || [] : [];

  // Get available subjects based on selected branch AND semester
  const availableSubjects: string[] = (branch && semester)
    ? (BRANCH_CONFIG[branch as keyof typeof BRANCH_CONFIG]?.subjects as Record<string, string[]>)?.[semester] || []
    : [];

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
      } else {
        alert('Please upload a PDF file');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file');
      return;
    }

    if (!branch || !semester || !subject) {
      alert('Please select branch, semester, and subject');
      return;
    }

    const token = sessionStorage.getItem('adminToken') || sessionStorage.getItem('authToken');
    if (!token) {
      setResult({ success: false, error: 'Login required to upload question papers.' });
      return;
    }

    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('branch', branch);
    formData.append('semester', semester);
    formData.append('subject', subject);
    // Ask backend to return extracted data for review instead of auto-saving
    formData.append('review', 'true');
    formData.append('uploadedBy', sessionStorage.getItem('authToken') ? 'faculty' : 'admin');

    try {
      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/upload-question-paper`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setResult(data);
        // Prepare editable copy for review UI when extracted data present
        if (data && data.extracted_data) {
          // deep clone to avoid mutating original
          const clone = JSON.parse(JSON.stringify(data.extracted_data));
          setEditableData(clone);

          // Prefer router state because sessionStorage is limited and can fail on large extracted payloads.
          saveReviewData(clone);
          navigate('/review-extracted', { state: { extractedData: clone } });
        }
        // Clear form on success
        setFile(null);
        setBranch('');
        setSemester('');
        setSubject('');
      } else {
        setResult({ success: false, error: data.error || 'Upload failed' });
      }
    } catch (error) {
      console.error('Upload error:', error);
      setResult({ success: false, error: 'Network error. Please try again.' });
    } finally {
      setUploading(false);
    }
  };

  const updateQuestionField = (pIdx: number, qIdx: number, field: string, value: any) => {
    setEditableData((prev: any) => {
      if (!prev) return prev;
      const copy = JSON.parse(JSON.stringify(prev));
      const q = copy.papers[pIdx].questions[qIdx];
      q[field] = value;
      return copy;
    });
  };

  const renumberPaperQuestions = (papers: any[], pIdx: number) => {
    const copy = JSON.parse(JSON.stringify(papers));
    const qs = copy[pIdx].questions || [];
    let seq = 1;
    for (let i = 0; i < qs.length; i++) {
      const txt = (qs[i].question_text || '').toString().trim();
      if (!txt) {
        // If question text empty, still assign next number (user may be filling it)
        qs[i].question_number = String(seq);
        seq += 1;
      } else {
        qs[i].question_number = String(seq);
        seq += 1;
      }
    }
    return copy;
  };

  const addQuestion = (pIdx: number) => {
    setEditableData((prev: any) => {
      if (!prev) return prev;
      const copy = JSON.parse(JSON.stringify(prev));
      const paper = copy.papers[pIdx] || { questions: [] };
      const newQ = {
        question_number: String((paper.questions?.length || 0) + 1),
        question_text: '',
        marks: 0,
        course_outcome: '',
        bloom_level: '',
        has_math: false,
        images: [],
        sub_questions: [],
      };
      paper.questions = paper.questions || [];
      paper.questions.push(newQ);
      copy.papers[pIdx] = paper;
      return copy;
    });
  };

  const deleteQuestion = (pIdx: number, qIdx: number) => {
    if (!confirm('Delete this question?')) return;
    setEditableData((prev: any) => {
      if (!prev) return prev;
      const copy = JSON.parse(JSON.stringify(prev));
      const paper = copy.papers[pIdx];
      if (!paper || !paper.questions) return prev;
      paper.questions.splice(qIdx, 1);
      // renumber
      const renum = renumberPaperQuestions(copy.papers, pIdx);
      return renum;
    });
  };

  const handleSaveToDb = async () => {
    if (!editableData || !result) return;
    const token = sessionStorage.getItem('adminToken') || sessionStorage.getItem('authToken');
    if (!token) { alert('Login required'); return; }

    try {
      const examInfo = {
        ...(editableData?.exam_info || result?.extracted_data?.exam_info || {}),
        subject_name: (editableData?.exam_info?.subject_name || result?.extracted_data?.exam_info?.subject_name || result?.detected_subject || subject || '').trim(),
        subject_code: (editableData?.exam_info?.subject_code || result?.extracted_data?.exam_info?.subject_code || result?.detected_subject_code || '').trim(),
        branch: (editableData?.exam_info?.branch || result?.extracted_data?.exam_info?.branch || branch || '').trim(),
        semester: (editableData?.exam_info?.semester || result?.extracted_data?.exam_info?.semester || semester || '').trim(),
      };

      const body = {
        json_file: result.json_file,
        branch: examInfo.branch || branch,
        semester: examInfo.semester || semester,
        subject: examInfo.subject_name || subject,
        subject_code: examInfo.subject_code || '',
        papers_data: editableData.papers,
        exam_info: examInfo,
      };

      const resp = await fetch(`${API_CONFIG.BACKEND_URL}/api/save-extracted-paper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
        body: JSON.stringify(body),
      });
      const d = await resp.json();
      if (resp.ok) {
        setResult(prev => ({
          ...(prev as any),
          paper_id: d.paper_id,
          saved_to_db: true,
          similarity: d.similarity,
        }));
        setEditableData(null);
        fetchRecentPapers();
        if (d.similarity?.status === 'completed') {
          alert(
            `Saved to database and similarity processing completed.\n` +
            `${d.similarity.processed} processed, ${d.similarity.duplicates} duplicates, ` +
            `${d.similarity.new_questions} new canonical questions.`
          );
        } else if (d.similarity?.status === 'failed') {
          alert(
            `Saved to database, but similarity processing failed: ` +
            `${d.similarity.error || 'Unknown error'}`
          );
        } else {
          alert('Saved to database successfully');
        }
      } else {
        alert('Save failed: ' + (d.error || 'Unknown'));
      }
    } catch (err) {
      console.error(err);
      alert('Network error while saving');
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 py-6 md:px-6">
      <div className="rounded-[28px] border border-[#e7dcc7] bg-[#f7f1e9]/90 p-6 shadow-[0_10px_30px_rgba(15,23,42,0.06)] md:p-8">
        <h2 className="text-[clamp(2.1rem,3vw,3rem)] font-black tracking-[-0.06em] text-[#1f2937] leading-none">
          Upload Question Paper
        </h2>

        <p className="mt-5 max-w-3xl text-lg leading-8 text-[#4b5563]">
          Upload a PDF question paper to automatically extract questions using OCR
          and store them in the database.
        </p>

        <div
          className={`mt-8 rounded-[22px] border-2 border-dashed p-8 text-center transition-all duration-200 md:p-10 ${
            dragActive
              ? 'border-[#f2a55a] bg-[#fff5eb] shadow-inner'
              : 'border-[#d9d1c6] bg-transparent'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {file ? (
            <div className="space-y-4">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-[#d7d1c7] bg-[#f5f2ee] text-[#1f2937]">
                <FileText className="h-11 w-11" strokeWidth={1.8} />
              </div>
              <p className="text-2xl font-semibold text-[#1f2937]">{file.name}</p>
              <p className="text-base text-[#6b7280]">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <button
                onClick={() => setFile(null)}
                className="inline-flex items-center gap-2 rounded-full border border-[#e5d4c7] bg-white px-4 py-2 text-sm font-semibold text-[#c2410c] transition hover:bg-[#fff7ed]"
              >
                <span className="text-base">×</span>
                Remove file
              </button>
            </div>
          ) : (
            <div className="space-y-5">
              <div className="mx-auto flex h-24 w-24 items-center justify-center text-[#1e293b]">
                <FileText className="h-20 w-20" strokeWidth={1.4} />
              </div>
              <p className="text-[2rem] font-medium leading-tight text-[#1f2937]">
                Drag and drop your PDF here
              </p>
              <p className="text-lg text-[#475569]">or</p>
              <label className="inline-block cursor-pointer">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <span className="inline-flex items-center justify-center rounded-xl bg-[#1f68d8] px-7 py-3 text-lg font-semibold text-white shadow-[0_10px_20px_rgba(31,104,216,0.25)] transition hover:bg-[#175dc8]">
                  Browse Files
                </span>
              </label>
            </div>
          )}
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <div>
            <label className="mb-2 block text-base font-semibold text-[#374151]">
              Branch <span className="text-[#ef4444]">*</span>
            </label>
            <select
              value={branch}
              onChange={(e) => {
                setBranch(e.target.value);
                setSemester('');
                setSubject('');
              }}
              className="h-14 w-full rounded-xl border border-[#d5cec3] bg-white/80 px-4 text-base text-[#1f2937] shadow-sm outline-none transition focus:border-[#f2a55a] focus:ring-2 focus:ring-[#f7d7b7]"
            >
              <option value="">Select Branch</option>
              {Object.keys(BRANCH_CONFIG).map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-base font-semibold text-[#374151]">
              Semester <span className="text-[#ef4444]">*</span>
            </label>
            <select
              value={semester}
              onChange={(e) => { setSemester(e.target.value); setSubject(''); }}
              disabled={!branch}
              className="h-14 w-full rounded-xl border border-[#d5cec3] bg-white/80 px-4 text-base text-[#1f2937] shadow-sm outline-none transition focus:border-[#f2a55a] focus:ring-2 focus:ring-[#f7d7b7] disabled:cursor-not-allowed disabled:bg-[#f3f4f6] disabled:text-[#9ca3af]"
            >
              <option value="">Select Semester</option>
              {availableSemesters.map((sem) => (
                <option key={sem} value={sem}>Semester {sem}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-base font-semibold text-[#374151]">
              Subject <span className="text-[#ef4444]">*</span>
            </label>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={!branch || !semester}
              className="h-14 w-full rounded-xl border border-[#d5cec3] bg-white/80 px-4 text-base text-[#1f2937] shadow-sm outline-none transition focus:border-[#f2a55a] focus:ring-2 focus:ring-[#f7d7b7] disabled:cursor-not-allowed disabled:bg-[#f3f4f6] disabled:text-[#9ca3af]"
            >
              <option value="">{!branch ? 'Select Branch first' : !semester ? 'Select Semester first' : 'Select Subject'}</option>
              {availableSubjects.map((subj) => (
                <option key={subj} value={subj}>{subj}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleUpload}
          disabled={uploading || !file}
          className={`mt-8 flex w-full items-center justify-center rounded-xl py-4 text-xl font-bold text-white shadow-[0_12px_22px_rgba(240,144,49,0.25)] transition ${
            uploading || !file
              ? 'cursor-not-allowed bg-[#d1d5db] text-[#ffffff] shadow-none'
              : 'bg-[#f7a14d] hover:bg-[#f1922d]'
          }`}
        >
          {uploading ? (
            <span className="flex items-center justify-center gap-3">
              <svg
                className="h-5 w-5 animate-spin"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Processing...
            </span>
          ) : (
            'Upload and Extract Questions'
          )}
        </button>

        {/* Result Display */}
        {result && (
          <div
            className={`mt-6 p-6 rounded-lg ${
              result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}
          >
            {result.success ? (
              <div className="space-y-4">
                <div className="flex items-start">
                  <span className="text-2xl mr-3">âœ…</span>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-green-800 mb-2">
                      Success!
                    </h3>
                    <p className="text-green-700 mb-3">{result.message}</p>
                    
                    {result.extracted_data && (
                      <div className="bg-white rounded-lg p-4 space-y-2">
                        <p className="font-semibold text-gray-800">
                          Extraction Summary:
                        </p>
                        <ul className="list-disc list-inside text-gray-700 space-y-1">
                          <li>
                            Papers processed: {result.extracted_data.total_papers}
                          </li>
                          <li>
                            Questions extracted: {result.extracted_data.papers.reduce((sum: number, p: any) => sum + p.questions.length, 0)}
                          </li>
                          <li>
                            File: {result.filename}
                          </li>
                          {result.extraction_source && (
                            <li>
                              Extraction source: <span className="font-medium text-blue-700">{result.extraction_source}</span>
                            </li>
                          )}
                          {result.detected_subject && (
                            <li>
                              Detected subject: <span className="font-medium text-blue-700">{result.detected_subject}</span>
                            </li>
                          )}
                          {result.detected_subject_code && (
                            <li>
                              Subject code: <span className="font-medium text-blue-700">{result.detected_subject_code}</span>
                            </li>
                          )}
                          {result.paper_id && (
                            <li>
                              Saved to DB â€” Paper ID: {result.paper_id}
                            </li>
                          )}
                        </ul>
                      </div>
                    )}

                    {result.extracted_data && result.extracted_data.papers.length > 0 && result.extracted_data.papers[0].questions.length > 0 && (
                      <div className="bg-white rounded-lg p-4 mt-3 max-h-64 overflow-y-auto">
                        <p className="font-semibold text-gray-800 mb-2">
                          Sample Questions:
                        </p>
                        <div className="space-y-2">
                          {result.extracted_data.papers[0].questions.slice(0, 3).map((q, idx) => (
                            <div key={idx} className="text-sm text-gray-700 border-l-2 border-blue-500 pl-3">
                              <p className="font-medium">
                                Q{q.question_number}: {q.question_text.substring(0, 100)}
                                {q.question_text.length > 100 ? '...' : ''}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                Marks: {q.marks} {q.course_outcome ? `| ${q.course_outcome}` : ''} {q.has_math ? 'ðŸ“' : ''}
                              </p>
                            </div>
                          ))}
                          {result.extracted_data.papers[0].questions.length > 3 && (
                            <p className="text-xs text-gray-500 italic">
                              ... and {result.extracted_data.papers[0].questions.length - 3} more questions
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                      {/* Review / Edit panel shown when editableData is available */}
                      {editableData && (
                        <div className="bg-white rounded-lg p-4 mt-4">
                          <div className="flex items-center justify-between mb-3">
                            <p className="font-semibold">Review & Edit Extracted Questions</p>
                            <div className="space-x-2">
                              <button onClick={handleSaveToDb} className="px-3 py-1 bg-green-600 text-white rounded">Save to DB</button>
                              <button onClick={() => setEditableData(null)} className="px-3 py-1 bg-gray-200 rounded">Cancel</button>
                            </div>
                          </div>
                          <div className="space-y-4 max-h-96 overflow-y-auto">
                            {editableData.papers.map((p: any, pIdx: number) => (
                              <div key={pIdx} className="border rounded p-3">
                                <div className="font-medium mb-2">Paper {p.paper_number || pIdx+1} {p.paper_name ? `- ${p.paper_name}` : ''}</div>
                                <div className="flex justify-end mb-2">
                                  <button onClick={() => addQuestion(pIdx)} className="px-2 py-1 bg-blue-600 text-white rounded text-sm">Add question</button>
                                </div>
                                {p.questions.map((q: any, qIdx: number) => (
                                  <div key={qIdx} className="mb-3">
                                    <div className="flex items-center justify-between">
                                      <div className="text-sm text-gray-600 mb-1">Q{q.question_number || (qIdx+1)}</div>
                                      <button onClick={() => deleteQuestion(pIdx, qIdx)} className="text-sm text-red-600">Delete</button>
                                    </div>
                                    <textarea
                                      value={q.question_text}
                                      onChange={(e) => updateQuestionField(pIdx, qIdx, 'question_text', e.target.value)}
                                      className="w-full border rounded p-2 mb-1"
                                      rows={3}
                                    />
                                    <div className="flex items-center space-x-3 text-sm">
                                      <label className="flex items-center space-x-2">
                                        <span className="text-xs">Marks</span>
                                        <input type="number" value={q.marks || 0} onChange={(e) => updateQuestionField(pIdx, qIdx, 'marks', parseInt(e.target.value || '0'))} className="w-20 p-1 border rounded" />
                                      </label>
                                      <label className="flex items-center space-x-2">
                                        <span className="text-xs">CO</span>
                                        <input
                                          type="text"
                                          value={q.course_outcome || ''}
                                          onChange={(e) => updateQuestionField(pIdx, qIdx, 'course_outcome', e.target.value)}
                                          placeholder="CO1"
                                          className="w-20 p-1 border rounded"
                                          aria-label={`Course outcome for question ${q.question_number || qIdx + 1}`}
                                        />
                                      </label>
                                      <label className="flex items-center space-x-2">
                                        <input type="checkbox" checked={!!q.has_math} onChange={(e) => updateQuestionField(pIdx, qIdx, 'has_math', e.target.checked)} />
                                        <span className="text-xs">Has Math</span>
                                      </label>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-start">
                <span className="text-2xl mr-3">âŒ</span>
                <div>
                  <h3 className="text-lg font-bold text-red-800 mb-2">
                    Upload Failed
                  </h3>
                  <p className="text-red-700">{result.error}</p>
                </div>
              </div>
            )}
          </div>
        )}

        

        {/* Instructions */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold text-blue-900 mb-2">ðŸ“‹ Instructions:</h4>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Upload PDF files only (max 50MB)</li>
            <li>The system uses OCR to extract questions from scanned PDFs</li>
            <li>Questions will be automatically stored in the database</li>
            <li>Processing may take 1-2 minutes depending on the file size</li>
            <li>Make sure the PDF has clear, readable text</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default QuestionPaperUpload;
