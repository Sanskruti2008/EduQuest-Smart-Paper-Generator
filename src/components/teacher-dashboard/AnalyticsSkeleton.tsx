export default function AnalyticsSkeleton() {
  return (
    <section id="analytics" className="px-4 pb-12 md:px-8">
      <div className="rounded-2xl bg-white/70 backdrop-blur-xl shadow-xl border border-white/60 p-6">
        <div className="h-5 w-40 rounded bg-slate-200/70 animate-pulse" />
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div key={item} className="h-48 rounded-2xl bg-white/80 border border-white/60 shadow-sm animate-pulse" />
          ))}
        </div>
      </div>
    </section>
  );
}
