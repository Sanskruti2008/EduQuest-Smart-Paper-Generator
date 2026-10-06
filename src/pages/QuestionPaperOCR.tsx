import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import QuestionPaperUpload from '../components/QuestionPaperUpload';

const QuestionPaperOCR: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link
                to="/teacher"
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Back to Dashboard
              </Link>
            </div>
            <h1 className="text-xl font-bold text-gray-900">
              Question Paper OCR
            </h1>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Info Banner */}
        <div className="mb-8 bg-blue-600 text-white rounded-lg p-6 shadow-lg">
          <h2 className="text-2xl font-bold mb-2">
            🚀 Automated Question Extraction
          </h2>
          <p className="text-blue-100 text-lg">
            Upload your MSBTE question papers and let AI extract all questions automatically!
          </p>
        </div>

        {/* Upload Component */}
        <QuestionPaperUpload />

        {/* Features Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-4xl mb-3">🔍</div>
            <h3 className="font-bold text-gray-800 mb-2">OCR Technology</h3>
            <p className="text-gray-600 text-sm">
              Advanced OCR extracts text from scanned PDFs with high accuracy using Tesseract
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-4xl mb-3">🧠</div>
            <h3 className="font-bold text-gray-800 mb-2">Smart Parsing</h3>
            <p className="text-gray-600 text-sm">
              Intelligent parsing identifies questions, marks, and course outcomes automatically
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-4xl mb-3">💾</div>
            <h3 className="font-bold text-gray-800 mb-2">Database Storage</h3>
            <p className="text-gray-600 text-sm">
              All questions are stored in SQLite database for easy search and reuse
            </p>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mt-12 bg-white rounded-lg shadow-md p-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-6">
            How It Works
          </h3>
          <div className="space-y-6">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                1
              </div>
              <div className="ml-4">
                <h4 className="font-semibold text-gray-800 mb-1">Upload PDF</h4>
                <p className="text-gray-600 text-sm">
                  Upload your question paper PDF (supports scanned documents)
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                2
              </div>
              <div className="ml-4">
                <h4 className="font-semibold text-gray-800 mb-1">OCR Processing</h4>
                <p className="text-gray-600 text-sm">
                  Advanced OCR converts images to text with preprocessing for better accuracy
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                3
              </div>
              <div className="ml-4">
                <h4 className="font-semibold text-gray-800 mb-1">Question Extraction</h4>
                <p className="text-gray-600 text-sm">
                  AI parses the text to identify questions, marks, and course outcomes
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                4
              </div>
              <div className="ml-4">
                <h4 className="font-semibold text-gray-800 mb-1">Database Storage</h4>
                <p className="text-gray-600 text-sm">
                  Questions are stored in SQLite with full metadata for easy retrieval
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Supported Formats Section */}
        <div className="mt-8 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg shadow-md p-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-4">
            Supported Question Formats
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4">
              <code className="text-blue-600 font-mono">Q1. Attempt any FIVE (20)</code>
              <p className="text-gray-600 mt-2">Main question with total marks</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <code className="text-blue-600 font-mono">a) CO1 What is...?</code>
              <p className="text-gray-600 mt-2">Sub-question with course outcome</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <code className="text-blue-600 font-mono">q) 3 Attempt any THREE (12)</code>
              <p className="text-gray-600 mt-2">Alternative main question format</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <code className="text-blue-600 font-mono">i) CO2 Define the term...</code>
              <p className="text-gray-600 mt-2">Roman numeral sub-questions</p>
            </div>
          </div>
        </div>

        {/* API Endpoints Section */}
        <div className="mt-8 bg-gray-900 text-white rounded-lg shadow-md p-8">
          <h3 className="text-2xl font-bold mb-4">API Endpoints</h3>
          <div className="space-y-3 font-mono text-sm">
            <div className="bg-gray-800 rounded p-3">
              <span className="text-green-400">POST</span>
              <span className="ml-3">/api/upload-question-paper</span>
              <p className="text-gray-400 text-xs mt-1">Upload and extract questions from PDF</p>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <span className="text-blue-400">GET</span>
              <span className="ml-3">/api/questions</span>
              <p className="text-gray-400 text-xs mt-1">Retrieve all questions with filters</p>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <span className="text-blue-400">GET</span>
              <span className="ml-3">/api/questions/search?q=text</span>
              <p className="text-gray-400 text-xs mt-1">Search questions by text content</p>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <span className="text-blue-400">GET</span>
              <span className="ml-3">/api/papers/:id</span>
              <p className="text-gray-400 text-xs mt-1">Get specific paper with all questions</p>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <span className="text-blue-400">GET</span>
              <span className="ml-3">/api/stats</span>
              <p className="text-gray-400 text-xs mt-1">Database statistics</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuestionPaperOCR;
