import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, X, CheckCircle } from 'lucide-react';

interface SimilarQuestion {
  id: number;
  text: string;
  subject: string;
  class: string;
  similarityScore: number;
  matchPercentage: string;
}

interface SimilarQuestionsProps {
  questions: SimilarQuestion[];
  onClose: () => void;
  onContinue: () => void;
}

export const SimilarQuestions: React.FC<SimilarQuestionsProps> = ({ questions, onClose, onContinue }) => {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertCircle size={24} />
              <div>
                <h3 className="font-bold text-lg">Similar Questions Detected</h3>
                <p className="text-sm text-white/90">{questions.length} similar question{questions.length !== 1 ? 's' : ''} found</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="hover:bg-white/20 rounded-lg p-2 transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(80vh-180px)]">
            <p className="text-gray-600 mb-4">
              We found questions similar to yours in our database. Review them to avoid duplication:
            </p>

            <div className="space-y-3">
              {questions.map((question, index) => (
                <motion.div
                  key={question.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="border border-gray-200 rounded-lg p-4 hover:border-amber-300 hover:bg-amber-50/50 transition-all"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex-1">
                      <p className="text-gray-800 font-medium">{question.text}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        question.similarityScore >= 80 
                          ? 'bg-red-100 text-red-700' 
                          : question.similarityScore >= 60 
                          ? 'bg-amber-100 text-amber-700' 
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {question.matchPercentage} match
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span className="bg-gray-100 px-2 py-0.5 rounded">
                      {question.subject}
                    </span>
                    <span className="bg-gray-100 px-2 py-0.5 rounded">
                      Class {question.class}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>💡 Tip:</strong> Consider reviewing these similar questions before continuing. 
                You can modify your question to make it more unique or use these as inspiration.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 p-4 bg-gray-50 flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors font-medium"
            >
              Review & Edit
            </button>
            <button
              onClick={onContinue}
              className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all font-medium flex items-center gap-2"
            >
              <CheckCircle size={18} />
              Continue Anyway
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
