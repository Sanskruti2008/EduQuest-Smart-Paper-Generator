import { CalendarClock, CheckCheck, Clock3, ListTodo } from 'lucide-react';
import SectionHeader from './SectionHeader';

const assignedTasks = [
  {
    title: 'Review Midterm Question Paper',
    subject: 'DBMS',
    due: 'Due today, 5:00 PM',
    status: 'In Review',
    priority: 'High',
    detail: 'Check Bloom alignment, marks distribution, and question coverage before final approval.'
  },
  {
    title: 'Validate Unit Test Blueprint',
    subject: 'Operating Systems',
    due: 'Due tomorrow, 11:30 AM',
    status: 'Pending',
    priority: 'Medium',
    detail: 'Confirm the test pattern matches the syllabus and review difficulty balance.'
  },
  {
    title: 'Approve Practical Assessment Sheet',
    subject: 'Software Engineering',
    due: 'Due Friday, 2:30 PM',
    status: 'Assigned',
    priority: 'Low',
    detail: 'Review rubric clarity, practical marks, and evaluation structure before sharing.'
  }
];

export default function AssignedTasksSection({ onSectionSelect }: { onSectionSelect?: (section: string) => void }) {
  return (
    <section id="assigned-tasks" className="px-4 pb-8 md:px-8">
      <SectionHeader
        title="Assigned Tasks"
        subtitle="All tasks and review items assigned to you are listed here."
        icon={ListTodo}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {assignedTasks.map((task) => (
          <div key={task.title} className="rounded-2xl border border-white/60 bg-white/70 p-5 shadow-xl backdrop-blur-xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-800">{task.title}</p>
                <p className="mt-1 text-xs text-slate-500">{task.subject}</p>
              </div>
              <span
                className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-semibold ${
                  task.status === 'In Review'
                    ? 'bg-amber-100 text-amber-700'
                    : task.status === 'Pending'
                      ? 'bg-orange-100 text-orange-700'
                      : 'bg-emerald-100 text-emerald-700'
                }`}
              >
                {task.status}
              </span>
            </div>

            <p className="mt-4 text-sm text-slate-600">{task.detail}</p>

            <div className="mt-4 space-y-2 text-[11px] text-slate-600">
              <div className="flex items-center gap-2">
                <CalendarClock className="h-3.5 w-3.5 text-slate-500" />
                {task.due}
              </div>
              <div className="flex items-center gap-2">
                <Clock3 className="h-3.5 w-3.5 text-slate-500" />
                Priority: {task.priority}
              </div>
            </div>

            <button
              type="button"
              onClick={() => onSectionSelect && onSectionSelect('moderation')}
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:shadow-md"
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Review task
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
