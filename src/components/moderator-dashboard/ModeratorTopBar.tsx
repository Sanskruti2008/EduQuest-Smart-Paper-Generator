import { BadgeCheck, CheckCircle2, MessageSquareDiff, UserCircle2, XCircle } from 'lucide-react';

export type ModeratorPaperMeta = {
  due: string;
  status: string;
};

type ModeratorTopBarProps = {
  activePaper: ModeratorPaperMeta;
  profile: {
    name: string;
    role: string;
    email: string;
    note: string;
  };
  profileOpen: boolean;
  onToggleProfile: () => void;
  onComment: () => void;
  onReject: () => void;
  onApprove: () => void;
};

export default function ModeratorTopBar({
  activePaper,
  profile,
  profileOpen,
  onToggleProfile,
  onComment,
  onReject,
  onApprove
}: ModeratorTopBarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/40 bg-white/70 backdrop-blur-xl shadow-sm">
      <div className="px-4 py-4 md:px-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium text-amber-600">Moderation Console</p>
          <h1 className="text-2xl font-bold text-slate-800">Faculty Review Panel</h1>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs text-slate-500">Due: {activePaper.due}</p>
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
              activePaper.status === 'Approved'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : activePaper.status === 'Rejected'
                ? 'bg-rose-50 text-rose-700 border-rose-200'
                : activePaper.status === 'Needs Corrections'
                ? 'bg-amber-50 text-amber-700 border-amber-200'
                : 'bg-slate-50 text-slate-600 border-slate-200'
            }`}>
              {activePaper.status}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onToggleProfile}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 font-semibold text-slate-700 transition hover:border-amber-300"
          >
            <UserCircle2 className="h-4 w-4" /> Profile
          </button>
          <button
            onClick={onComment}
            className="flex items-center gap-2 px-4 py-2 text-slate-700 bg-white rounded-xl font-semibold border border-slate-200 hover:border-amber-300 transition"
          >
            <MessageSquareDiff className="h-4 w-4" /> Comment
          </button>
          <button
            onClick={onReject}
            className="flex items-center gap-2 px-4 py-2 text-rose-700 bg-rose-50 rounded-xl font-semibold hover:bg-rose-100 transition"
          >
            <XCircle className="h-4 w-4" /> Reject
          </button>
          <button
            onClick={onApprove}
            className="flex items-center gap-2 px-4 py-2 text-emerald-700 bg-emerald-50 rounded-xl font-semibold hover:bg-emerald-100 transition"
          >
            <CheckCircle2 className="h-4 w-4" /> Approve
          </button>
        </div>
      </div>
      {profileOpen && (
        <div className="border-t border-white/40 bg-white/80 px-4 pb-4 md:px-8">
          <div className="mt-4 grid gap-4 rounded-2xl border border-amber-100 bg-gradient-to-br from-amber-50 to-white p-4 shadow-sm sm:grid-cols-[auto_1fr] sm:items-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-lg">
              <BadgeCheck className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-semibold text-amber-600">Reviewer Profile</p>
              <h2 className="text-lg font-bold text-slate-800">{profile.name}</h2>
              <p className="text-sm text-slate-500">{profile.role} • {profile.email}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{profile.note}</p>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
