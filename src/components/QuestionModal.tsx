import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, Plus, Image, Upload, Trash2 } from 'lucide-react';
import { Question, useQuestionBank } from '../context/QuestionBankContext';
import { BRANCHES, SEMESTERS, formatBranchSemester, parseBranchSemesterLabel } from '../utils/constants';

interface QuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  question?: Question | null;
  defaultGrade?: string;
  defaultYear?: string;
  defaultSubject?: string;
}

const QuestionModal = ({ isOpen, onClose, question, defaultGrade, defaultYear, defaultSubject }: QuestionModalProps) => {
  const { addQuestion, updateQuestion } = useQuestionBank();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [formData, setFormData] = useState({
    text: '',
    chapter: '',
    subject: '',
    grade: '',
    year: new Date().getFullYear().toString(),
    difficulty: 'Medium' as 'Easy' | 'Medium' | 'Hard',
    marks: 5,
    type: 'Short Answer',
    tags: [] as string[],
    image: '' as string,
  });

  const [tagInput, setTagInput] = useState('');
  const [branchSelection, setBranchSelection] = useState('');
  const [semesterSelection, setSemesterSelection] = useState('');

  const updateGradeField = (branch: string, semester: string) => {
    setFormData(prev => ({
      ...prev,
      grade: formatBranchSemester(branch, semester)
    }));
  };

  useEffect(() => {
    const resolvedGrade = question?.grade ?? defaultGrade ?? '';
    const { branch, semester } = parseBranchSemesterLabel(resolvedGrade);
    setBranchSelection(branch);
    setSemesterSelection(semester);

    const resolvedYear = question?.year ?? defaultYear ?? new Date().getFullYear().toString();

    if (question) {
      setFormData({
        text: question.text,
        chapter: question.chapter,
        subject: question.subject,
        grade: resolvedGrade,
        year: resolvedYear,
        difficulty: question.difficulty,
        marks: question.marks,
        type: question.type,
        tags: question.tags || [],
        image: question.image || '',
      });
    } else {
      setFormData({
        text: '',
        chapter: '',
        subject: defaultSubject || '',
        grade: resolvedGrade,
        year: resolvedYear,
        difficulty: 'Medium',
        marks: 5,
        type: 'Short Answer',
        tags: [],
        image: '',
      });
    }
  }, [question, isOpen, defaultGrade, defaultYear, defaultSubject]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.grade) {
      alert('Please select a branch and semester.');
      return;
    }
    
    if (question) {
      updateQuestion(question.id, formData);
    } else {
      addQuestion(formData);
    }
    
    onClose();
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData({ ...formData, tags: formData.tags.filter(t => t !== tag) });
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check file size (max 2MB)
      if (file.size > 2 * 1024 * 1024) {
        alert('Image size should be less than 2MB');
        return;
      }
      
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, image: reader.result as string });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = () => {
    setFormData({ ...formData, image: '' });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />
        
        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              {question ? 'Edit Question' : 'Add New Question'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Question Text */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Question Text <span className="text-red-500">*</span>
              </label>
              <textarea
                required
                value={formData.text}
                onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all resize-none"
                rows={4}
                placeholder="Enter the question text..."
              />
            </div>

            {/* Question Image */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <span className="flex items-center gap-2">
                  <Image className="w-4 h-4" />
                  Question Image (Optional)
                </span>
              </label>
              
              {formData.image ? (
                <div className="relative rounded-lg border border-gray-200 overflow-hidden">
                  <img 
                    src={formData.image} 
                    alt="Question" 
                    className="w-full max-h-48 object-contain bg-gray-50"
                  />
                  <button
                    type="button"
                    onClick={handleRemoveImage}
                    className="absolute top-2 right-2 p-2 rounded-lg bg-red-500 hover:bg-red-600 text-white transition-all shadow-lg"
                    title="Remove image"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-gray-400 hover:bg-gray-50 transition-all"
                >
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Click to upload an image</p>
                  <p className="text-xs text-gray-400 mt-1">PNG, JPG up to 2MB</p>
                </div>
              )}
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>

            {/* Subject & Chapter */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Subject <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  type="text"
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all"
                  placeholder="e.g., Mathematics"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Chapter <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  type="text"
                  value={formData.chapter}
                  onChange={(e) => setFormData({ ...formData, chapter: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all"
                  placeholder="e.g., Calculus"
                />
              </div>
            </div>

            {/* Branch, Semester & Year */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Branch <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={branchSelection}
                  onChange={(e) => {
                    const value = e.target.value;
                    setBranchSelection(value);
                    updateGradeField(value, semesterSelection);
                  }}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all bg-white"
                >
                  <option value="">Select Branch</option>
                  {BRANCHES.map(branch => (
                    <option key={branch} value={branch}>{branch}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Semester <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={semesterSelection}
                  onChange={(e) => {
                    const value = e.target.value;
                    setSemesterSelection(value);
                    updateGradeField(branchSelection, value);
                  }}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all bg-white"
                >
                  <option value="">Select Semester</option>
                  {SEMESTERS.map(semester => (
                    <option key={semester} value={semester}>{semester}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Year <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all bg-white"
                >
                  {[2025, 2024, 2023, 2022, 2021].map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Difficulty & Marks */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Difficulty <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.difficulty}
                  onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as 'Easy' | 'Medium' | 'Hard' })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all bg-white"
                >
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Marks <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  type="number"
                  min="1"
                  max="100"
                  value={formData.marks}
                  onChange={(e) => setFormData({ ...formData, marks: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all"
                />
              </div>
            </div>

            {/* Question Type */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Question Type <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all bg-white"
              >
                <option value="Short Answer">Short Answer</option>
                <option value="Long Answer">Long Answer</option>
                <option value="Numerical">Numerical</option>
                <option value="Multiple Choice">Multiple Choice</option>
                <option value="True/False">True/False</option>
                <option value="Fill in the Blanks">Fill in the Blanks</option>
                <option value="Programming">Programming</option>
              </select>
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Tags (Optional)
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  className="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 outline-none transition-all"
                  placeholder="Add a tag..."
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="px-4 py-2.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold transition-all"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
              {formData.tags.length > 0 && (
                <div className="flex gap-2 flex-wrap">
                  {formData.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 text-gray-700 text-sm"
                    >
                      #{tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="hover:text-red-600 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 hover:bg-gray-50 font-semibold text-gray-700 transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-white font-semibold transition-all flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                {question ? 'Update Question' : 'Add Question'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default QuestionModal;
