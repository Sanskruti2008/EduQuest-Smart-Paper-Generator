import { AlertCircle, Layers, MessageCircle, Sparkles } from 'lucide-react';
import SectionHeader from './SectionHeader';

export default function SuggestionsSection() {
  return (
    <section id="ai-suggestions" className="px-4 pb-8 md:px-8">
      <SectionHeader
        title="AI Suggestions & Signals"
        subtitle="Recommendations from EduQuest intelligence and activity alerts."
        icon={Sparkles}
      />
      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6">
          <h3 className="text-lg font-semibold">AI Suggestions</h3>
          <div className="mt-4 grid gap-3">
            {[
              { title: 'Frequently Asked Topics', info: 'SQL joins, normalization, indexing' },
              { title: 'Weak Syllabus Areas', info: 'Transaction recovery and deadlocks' },
              { title: 'University Trends', info: 'Case studies on ER design are trending' },
              { title: 'Predicted Important Questions', info: 'Design a hospital database schema' }
            ].map((item) => (
              <div key={item.title} className="rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
                <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                <p className="mt-2 text-xs text-slate-500">{item.info}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6">
          <h3 className="text-lg font-semibold">Notifications & Activity</h3>
          <div className="mt-4 space-y-3">
            {[
              { icon: MessageCircle, title: 'Moderator feedback', detail: 'Adjust difficulty balance in Unit 3.' },
              { icon: AlertCircle, title: 'Approval alert', detail: 'DBMS Paper 2 approved by admin.' },
              { icon: Layers, title: 'AI recommendation', detail: 'Add more numerical questions.' }
            ].map((item) => (
              <div key={item.title} className="flex items-start gap-3 rounded-2xl bg-white/80 border border-white/60 p-4 shadow-sm">
                <item.icon className="h-5 w-5 text-amber-600" />
                <div>
                  <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
