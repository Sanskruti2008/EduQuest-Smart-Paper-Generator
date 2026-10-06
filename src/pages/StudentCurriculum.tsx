import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, BookOpen, Download, ExternalLink, FileText, GraduationCap, ChevronRight } from 'lucide-react';

interface CurriculumItem {
  id: string;
  name: string;
  description: string;
  pdfUrl?: string;
  externalUrl?: string;
}

interface BranchCurriculum {
  branch: string;
  fullName: string;
  icon: string;
  semesters: {
    semester: number;
    subjects: CurriculumItem[];
  }[];
}

const StudentCurriculum = () => {
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  const [selectedSemester, setSelectedSemester] = useState<number | null>(null);

  // Sample curriculum data - can be replaced with API calls
  const curriculumData: BranchCurriculum[] = [
    {
      branch: 'CS',
      fullName: 'Computer Science & Engineering',
      icon: '💻',
      semesters: [
        {
          semester: 1,
          subjects: [
            { id: 'cs1-1', name: 'Engineering Mathematics I', description: 'Calculus, Linear Algebra, and Differential Equations', pdfUrl: '/curriculum/cs/sem1/math1.pdf' },
            { id: 'cs1-2', name: 'Engineering Physics', description: 'Classical Mechanics, Thermodynamics, and Optics', pdfUrl: '/curriculum/cs/sem1/physics.pdf' },
            { id: 'cs1-3', name: 'Programming in C', description: 'Introduction to C Programming and Data Structures', pdfUrl: '/curriculum/cs/sem1/c-prog.pdf' },
            { id: 'cs1-4', name: 'Engineering Graphics', description: 'Technical Drawing and CAD', pdfUrl: '/curriculum/cs/sem1/graphics.pdf' },
          ],
        },
        {
          semester: 2,
          subjects: [
            { id: 'cs2-1', name: 'Engineering Mathematics II', description: 'Advanced Calculus and Statistics', pdfUrl: '/curriculum/cs/sem2/math2.pdf' },
            { id: 'cs2-2', name: 'Data Structures', description: 'Linear and Non-Linear Data Structures', pdfUrl: '/curriculum/cs/sem2/ds.pdf' },
            { id: 'cs2-3', name: 'Object Oriented Programming', description: 'OOP Concepts using C++ and Java', pdfUrl: '/curriculum/cs/sem2/oop.pdf' },
            { id: 'cs2-4', name: 'Digital Electronics', description: 'Logic Gates and Circuit Design', pdfUrl: '/curriculum/cs/sem2/de.pdf' },
          ],
        },
        {
          semester: 3,
          subjects: [
            { id: 'cs3-1', name: 'Database Management Systems', description: 'SQL, Normalization, and Transaction Management', pdfUrl: '/curriculum/cs/sem3/dbms.pdf' },
            { id: 'cs3-2', name: 'Computer Networks', description: 'Network Protocols and Architecture', pdfUrl: '/curriculum/cs/sem3/cn.pdf' },
            { id: 'cs3-3', name: 'Operating Systems', description: 'Process Management and Memory Management', pdfUrl: '/curriculum/cs/sem3/os.pdf' },
            { id: 'cs3-4', name: 'Design and Analysis of Algorithms', description: 'Algorithm Design Techniques and Complexity Analysis', pdfUrl: '/curriculum/cs/sem3/daa.pdf' },
          ],
        },
        {
          semester: 4,
          subjects: [
            { id: 'cs4-1', name: 'Web Technologies', description: 'HTML, CSS, JavaScript, and Web Development', pdfUrl: '/curriculum/cs/sem4/web.pdf' },
            { id: 'cs4-2', name: 'Software Engineering', description: 'SDLC, Testing, and Project Management', pdfUrl: '/curriculum/cs/sem4/se.pdf' },
            { id: 'cs4-3', name: 'Machine Learning', description: 'ML Algorithms and Applications', pdfUrl: '/curriculum/cs/sem4/ml.pdf' },
            { id: 'cs4-4', name: 'Cloud Computing', description: 'Cloud Services and Deployment Models', pdfUrl: '/curriculum/cs/sem4/cloud.pdf' },
          ],
        },
      ],
    },
    {
      branch: 'IT',
      fullName: 'Information Technology',
      icon: '⚡',
      semesters: [
        {
          semester: 1,
          subjects: [
            { id: 'it1-1', name: 'Engineering Mathematics I', description: 'Calculus, Linear Algebra, and Differential Equations', pdfUrl: '/curriculum/it/sem1/math1.pdf' },
            { id: 'it1-2', name: 'Engineering Physics', description: 'Classical Mechanics, Thermodynamics, and Optics', pdfUrl: '/curriculum/it/sem1/physics.pdf' },
            { id: 'it1-3', name: 'Programming Fundamentals', description: 'Introduction to Programming Concepts', pdfUrl: '/curriculum/it/sem1/prog.pdf' },
            { id: 'it1-4', name: 'Communication Skills', description: 'Technical Writing and Presentation', pdfUrl: '/curriculum/it/sem1/comm.pdf' },
          ],
        },
        {
          semester: 2,
          subjects: [
            { id: 'it2-1', name: 'Engineering Mathematics II', description: 'Advanced Calculus and Statistics', pdfUrl: '/curriculum/it/sem2/math2.pdf' },
            { id: 'it2-2', name: 'Data Structures & Algorithms', description: 'Linear and Non-Linear Data Structures', pdfUrl: '/curriculum/it/sem2/dsa.pdf' },
            { id: 'it2-3', name: 'Computer Organization', description: 'Digital Logic and Computer Architecture', pdfUrl: '/curriculum/it/sem2/co.pdf' },
            { id: 'it2-4', name: 'Database Systems', description: 'Database Design and SQL', pdfUrl: '/curriculum/it/sem2/db.pdf' },
          ],
        },
      ],
    },
    {
      branch: 'ME',
      fullName: 'Mechanical Engineering',
      icon: '⚙️',
      semesters: [
        {
          semester: 1,
          subjects: [
            { id: 'me1-1', name: 'Engineering Mathematics I', description: 'Calculus, Linear Algebra, and Differential Equations', pdfUrl: '/curriculum/me/sem1/math1.pdf' },
            { id: 'me1-2', name: 'Engineering Physics', description: 'Classical Mechanics, Thermodynamics, and Optics', pdfUrl: '/curriculum/me/sem1/physics.pdf' },
            { id: 'me1-3', name: 'Engineering Mechanics', description: 'Statics and Dynamics', pdfUrl: '/curriculum/me/sem1/mechanics.pdf' },
            { id: 'me1-4', name: 'Engineering Drawing', description: 'Technical Drawing and CAD', pdfUrl: '/curriculum/me/sem1/drawing.pdf' },
          ],
        },
        {
          semester: 2,
          subjects: [
            { id: 'me2-1', name: 'Engineering Mathematics II', description: 'Advanced Calculus and Statistics', pdfUrl: '/curriculum/me/sem2/math2.pdf' },
            { id: 'me2-2', name: 'Thermodynamics', description: 'Laws of Thermodynamics and Applications', pdfUrl: '/curriculum/me/sem2/thermo.pdf' },
            { id: 'me2-3', name: 'Manufacturing Processes', description: 'Casting, Welding, and Machining', pdfUrl: '/curriculum/me/sem2/mfg.pdf' },
            { id: 'me2-4', name: 'Material Science', description: 'Properties and Structure of Materials', pdfUrl: '/curriculum/me/sem2/materials.pdf' },
          ],
        },
      ],
    },
    {
      branch: 'EE',
      fullName: 'Electrical Engineering',
      icon: '⚡',
      semesters: [
        {
          semester: 1,
          subjects: [
            { id: 'ee1-1', name: 'Engineering Mathematics I', description: 'Calculus, Linear Algebra, and Differential Equations', pdfUrl: '/curriculum/ee/sem1/math1.pdf' },
            { id: 'ee1-2', name: 'Engineering Physics', description: 'Classical Mechanics, Thermodynamics, and Optics', pdfUrl: '/curriculum/ee/sem1/physics.pdf' },
            { id: 'ee1-3', name: 'Basic Electrical Engineering', description: 'Circuit Theory and Network Analysis', pdfUrl: '/curriculum/ee/sem1/bee.pdf' },
            { id: 'ee1-4', name: 'Workshop Practice', description: 'Electrical Wiring and Safety', pdfUrl: '/curriculum/ee/sem1/workshop.pdf' },
          ],
        },
        {
          semester: 2,
          subjects: [
            { id: 'ee2-1', name: 'Engineering Mathematics II', description: 'Advanced Calculus and Statistics', pdfUrl: '/curriculum/ee/sem2/math2.pdf' },
            { id: 'ee2-2', name: 'Electrical Machines', description: 'DC and AC Machines', pdfUrl: '/curriculum/ee/sem2/machines.pdf' },
            { id: 'ee2-3', name: 'Power Systems', description: 'Generation, Transmission, and Distribution', pdfUrl: '/curriculum/ee/sem2/power.pdf' },
            { id: 'ee2-4', name: 'Control Systems', description: 'Feedback Control and Stability', pdfUrl: '/curriculum/ee/sem2/control.pdf' },
          ],
        },
      ],
    },
    {
      branch: 'EC',
      fullName: 'Electronics & Communication',
      icon: '📡',
      semesters: [
        {
          semester: 1,
          subjects: [
            { id: 'ec1-1', name: 'Engineering Mathematics I', description: 'Calculus, Linear Algebra, and Differential Equations', pdfUrl: '/curriculum/ec/sem1/math1.pdf' },
            { id: 'ec1-2', name: 'Engineering Physics', description: 'Classical Mechanics, Thermodynamics, and Optics', pdfUrl: '/curriculum/ec/sem1/physics.pdf' },
            { id: 'ec1-3', name: 'Electronic Devices', description: 'Semiconductor Devices and Circuits', pdfUrl: '/curriculum/ec/sem1/devices.pdf' },
            { id: 'ec1-4', name: 'Circuit Theory', description: 'Network Analysis and Design', pdfUrl: '/curriculum/ec/sem1/circuit.pdf' },
          ],
        },
        {
          semester: 2,
          subjects: [
            { id: 'ec2-1', name: 'Engineering Mathematics II', description: 'Advanced Calculus and Statistics', pdfUrl: '/curriculum/ec/sem2/math2.pdf' },
            { id: 'ec2-2', name: 'Digital Electronics', description: 'Logic Gates and Sequential Circuits', pdfUrl: '/curriculum/ec/sem2/digital.pdf' },
            { id: 'ec2-3', name: 'Signals & Systems', description: 'Signal Processing and Analysis', pdfUrl: '/curriculum/ec/sem2/signals.pdf' },
            { id: 'ec2-4', name: 'Communication Systems', description: 'Analog and Digital Communication', pdfUrl: '/curriculum/ec/sem2/comm.pdf' },
          ],
        },
      ],
    },
    {
      branch: 'CE',
      fullName: 'Civil Engineering',
      icon: '🏗️',
      semesters: [
        {
          semester: 1,
          subjects: [
            { id: 'ce1-1', name: 'Engineering Mathematics I', description: 'Calculus, Linear Algebra, and Differential Equations', pdfUrl: '/curriculum/ce/sem1/math1.pdf' },
            { id: 'ce1-2', name: 'Engineering Physics', description: 'Classical Mechanics, Thermodynamics, and Optics', pdfUrl: '/curriculum/ce/sem1/physics.pdf' },
            { id: 'ce1-3', name: 'Engineering Mechanics', description: 'Statics and Dynamics', pdfUrl: '/curriculum/ce/sem1/mechanics.pdf' },
            { id: 'ce1-4', name: 'Building Materials', description: 'Properties and Testing of Construction Materials', pdfUrl: '/curriculum/ce/sem1/materials.pdf' },
          ],
        },
        {
          semester: 2,
          subjects: [
            { id: 'ce2-1', name: 'Engineering Mathematics II', description: 'Advanced Calculus and Statistics', pdfUrl: '/curriculum/ce/sem2/math2.pdf' },
            { id: 'ce2-2', name: 'Surveying', description: 'Land Surveying and Leveling', pdfUrl: '/curriculum/ce/sem2/survey.pdf' },
            { id: 'ce2-3', name: 'Strength of Materials', description: 'Stress, Strain, and Structural Analysis', pdfUrl: '/curriculum/ce/sem2/som.pdf' },
            { id: 'ce2-4', name: 'Fluid Mechanics', description: 'Fluid Properties and Flow', pdfUrl: '/curriculum/ce/sem2/fluid.pdf' },
          ],
        },
      ],
    },
  ];

  const selectedBranchData = curriculumData.find(b => b.branch === selectedBranch);
  const selectedSemesterData = selectedBranchData?.semesters.find(s => s.semester === selectedSemester);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link to="/student-dashboard" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <GraduationCap className="w-10 h-10 text-blue-600" />
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Branch-wise Curriculum
            </h1>
          </div>
          <p className="text-gray-600 mt-2">Access complete curriculum and syllabus for all branches and semesters</p>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {!selectedBranch ? (
          // Branch Selection View
          <>
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8 mb-12 border border-blue-100">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Select Your Branch 🎓</h2>
              <p className="text-gray-700">
                Choose your engineering branch to view the complete curriculum, subject-wise syllabus, and course content.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {curriculumData.map((branch) => (
                <div
                  key={branch.branch}
                  onClick={() => setSelectedBranch(branch.branch)}
                  className="bg-white rounded-xl p-8 border-2 border-gray-200 hover:border-blue-400 hover:shadow-xl transition-all duration-300 cursor-pointer group"
                >
                  <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">{branch.icon}</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{branch.branch}</h3>
                  <p className="text-gray-600 mb-4">{branch.fullName}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-blue-600 font-medium">{branch.semesters.length} Semesters</span>
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : !selectedSemester ? (
          // Semester Selection View
          <>
            <div className="mb-8">
              <button
                onClick={() => setSelectedBranch(null)}
                className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Branches
              </button>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-5xl">{selectedBranchData?.icon}</span>
                <div>
                  <h2 className="text-3xl font-bold text-gray-900">{selectedBranchData?.fullName}</h2>
                  <p className="text-gray-600">Select a semester to view subjects</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {selectedBranchData?.semesters.map((semester) => (
                <div
                  key={semester.semester}
                  onClick={() => setSelectedSemester(semester.semester)}
                  className="bg-white rounded-xl p-8 border-2 border-gray-200 hover:border-purple-400 hover:shadow-xl transition-all duration-300 cursor-pointer group text-center"
                >
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                    <span className="text-3xl font-bold text-white">{semester.semester}</span>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Semester {semester.semester}</h3>
                  <p className="text-gray-600 text-sm mb-4">{semester.subjects.length} Subjects</p>
                  <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-purple-600 mx-auto transition-all" />
                </div>
              ))}
            </div>
          </>
        ) : (
          // Subject List View
          <>
            <div className="mb-8">
              <button
                onClick={() => setSelectedSemester(null)}
                className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Semesters
              </button>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">{selectedSemester}</span>
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-gray-900">
                    {selectedBranchData?.fullName} - Semester {selectedSemester}
                  </h2>
                  <p className="text-gray-600">Complete subject curriculum and syllabus</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
              {selectedSemesterData?.subjects.map((subject, index) => (
                <div
                  key={subject.id}
                  className="bg-white rounded-xl p-6 border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                          <BookOpen className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-900">{subject.name}</h3>
                          <span className="text-sm text-gray-500">Subject {index + 1}</span>
                        </div>
                      </div>
                      <p className="text-gray-600 ml-13">{subject.description}</p>
                    </div>
                    <div className="flex flex-col gap-2">
                      {subject.pdfUrl && (
                        <button className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                          <Download className="w-4 h-4" />
                          Download
                        </button>
                      )}
                      {subject.externalUrl && (
                        <button className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium">
                          <ExternalLink className="w-4 h-4" />
                          View Online
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Additional Resources Section */}
            <div className="mt-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
              <div className="flex items-start gap-4">
                <FileText className="w-8 h-8 flex-shrink-0" />
                <div>
                  <h3 className="text-2xl font-bold mb-2">Need More Resources?</h3>
                  <p className="text-white/90 mb-4">
                    Access practice questions, previous year papers, and more learning materials for {selectedBranchData?.fullName}.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Link to="/student-question-bank">
                      <button className="px-6 py-2 bg-white text-blue-600 font-medium rounded-lg hover:bg-gray-100 transition-colors">
                        Question Bank
                      </button>
                    </Link>
                    <Link to="/previous-year-papers">
                      <button className="px-6 py-2 bg-white/10 text-white font-medium rounded-lg hover:bg-white/20 transition-colors border border-white/30">
                        Previous Papers
                      </button>
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default StudentCurriculum;
