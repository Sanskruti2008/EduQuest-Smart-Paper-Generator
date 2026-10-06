import { Bell } from 'lucide-react';
import SectionHeader from './SectionHeader';

const toastMessages = [
  {
    title: 'Moderator feedback received',
    message: 'Adjust Bloom distribution for DBMS Unit 3.',
    time: '2 min ago'
  },
  {
    title: 'AI Recommendation',
    message: 'Add more case studies on transactions.',
    time: '10 min ago'
  }
];

export default function NotificationsSection() {
  return (
    <section id="notifications" className="px-4 pb-12 md:px-8">
      <SectionHeader
        title="Notifications & Timeline"
        subtitle="Recent submissions, approvals, and AI updates in one place."
        icon={Bell}
      />
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6">
          <h3 className="text-lg font-semibold">Recent Submissions Timeline</h3>
          <div className="mt-4 space-y-4">
            {[
              { title: 'DBMS - Midterm Paper', status: 'Submitted to moderator', time: 'Today, 10:45 AM' },
              { title: 'OS - Practice Paper', status: 'Approved by admin', time: 'Yesterday, 6:20 PM' },
              { title: 'SE - Unit Test', status: 'AI draft ready', time: 'Yesterday, 1:05 PM' }
            ].map((event) => (
              <div key={event.title} className="flex items-start gap-3 rounded-2xl bg-white/80 p-4 shadow-sm border border-white/60">
                <span className="mt-1 h-2 w-2 rounded-full bg-amber-500"></span>
                <div>
                  <p className="text-sm font-semibold text-slate-800">{event.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{event.status}</p>
                  <p className="text-xs text-slate-400 mt-2">{event.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6">
          <h3 className="text-lg font-semibold">Toast Notifications</h3>
          <div className="mt-4 space-y-3">
            {toastMessages.map((toast) => (
              <div key={toast.title} className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
                <p className="text-sm font-semibold text-slate-800">{toast.title}</p>
                <p className="text-xs text-slate-500 mt-1">{toast.message}</p>
                <p className="text-[10px] text-slate-400 mt-2">{toast.time}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
