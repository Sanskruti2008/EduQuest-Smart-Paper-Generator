import { motion } from 'framer-motion';
import { ClipboardCheck, LayoutDashboard, Wand2, FolderOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import SectionHeader from './SectionHeader';

export default function OverviewSection({ onSectionSelect }: { onSectionSelect?: (section: string) => void }) {
  const navigate = useNavigate();

  return (
    <section id="dashboard" className="px-4 py-8 md:px-8">
      <SectionHeader
        title="Overview"
        subtitle="Your AI workspace at a glance with smart prompts and performance signals."
        icon={LayoutDashboard}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-white/60 bg-white/70 p-6 shadow-xl backdrop-blur-xl"
      >
        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold text-amber-600">Welcome back, Professor!</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900 md:text-3xl">Build your next exam with AI precision.</h2>
            <p className="mt-3 text-sm text-slate-600">
              Create question papers, review assigned work, and manage drafts without extra clutter.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onSectionSelect && onSectionSelect('my-papers')}
              className="rounded-2xl bg-gradient-to-r from-orange-500 to-amber-400 px-5 py-3 text-sm font-semibold text-white shadow-md transition hover:shadow-lg"
            >
              <Wand2 className="mr-2 inline-block h-4 w-4" /> View My Papers
            </button>
            <button
              onClick={() => onSectionSelect && onSectionSelect('my-papers')}
              className="rounded-2xl border border-white/60 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-amber-200"
            >
              <FolderOpen className="mr-2 inline-block h-4 w-4" /> View Drafts
            </button>
            <button
              onClick={() => onSectionSelect && onSectionSelect('moderation')}
              className="rounded-2xl border border-white/60 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-amber-200"
            >
              <ClipboardCheck className="mr-2 inline-block h-4 w-4" /> Review Queue
            </button>
          </div>
        </div>
      </motion.div>

    </section>
  );
}
