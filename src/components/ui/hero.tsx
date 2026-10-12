import { ArrowRight, Sparkles } from "lucide-react";
import { useEffect } from "react";
import { renderCanvas } from "./canvas";

export function Hero() {
  useEffect(() => {
    renderCanvas();
  }, []);

  return (
    <section id="home" className="relative min-h-[80vh] flex items-center">
      <div className="animate-fadeIn flex flex-col items-center justify-center px-4 text-center py-12 md:py-16 relative z-10 w-full">
        <div className="mb-6">
          <div className="relative flex items-center whitespace-nowrap rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-xs leading-6 text-[var(--text-muted)] shadow-sm hover:shadow-md transition-all">
            <Sparkles className="h-4 w-4 mr-2 text-[var(--accent-text)]" />
            Introducing EduQuest – Smart Question Paper Generator
            <button
              onClick={() => {
                document.getElementById('dashboard-selection')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="ml-2 flex items-center font-semibold text-[var(--accent-text)] hover:brightness-90 transition-colors"
            >
              <span className="absolute inset-0 flex" aria-hidden="true" />
              Explore{" "}
              <ArrowRight className="h-4 w-4 ml-1" aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="mb-8 mt-4">
          <div className="px-2">
            <div className="relative mx-auto h-full max-w-5xl border border-[var(--border)] bg-[var(--surface-2)] p-6 md:p-10 lg:p-14 rounded-[20px] shadow-[var(--shadow)]">
              <h1 className="select-none text-center text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight">
                <span className="text-[var(--text)]">
                  AI-Powered Question Paper Generator
                </span>
              </h1>
              <div className="flex items-center justify-center gap-1.5 mt-6">
                <span className="relative flex h-2.5 w-2.5 items-center justify-center">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                </span>
                <p className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">Available Now</p>
              </div>
            </div>
          </div>

          <h2 className="mt-10 text-2xl md:text-3xl font-bold text-[var(--text)]">
            Welcome to EduQuest – Smart Question Paper Generator
          </h2>

          <p className="mx-auto mt-3 mb-8 max-w-2xl px-6 text-base md:text-lg text-[var(--text-muted)] leading-relaxed">
            Create professional, well-structured question papers in minutes with AI assistance.
            <br className="hidden md:block" />
            Perfect for college and polytechnic faculty.
          </p>

          <div className="flex justify-center gap-4 flex-wrap">
            <button 
              onClick={() => {
                document.getElementById('dashboard-selection')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="flex items-center gap-2 px-8 py-3.5 md:px-10 md:py-4 text-sm md:text-base font-semibold rounded-xl bg-gradient-to-br from-[var(--accent-from)] to-[var(--accent-to)] text-white hover:-translate-y-px shadow-md hover:shadow-lg transition-all duration-200 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/30"
            >
              <Sparkles className="h-4 w-4 md:h-5 md:w-5" />
              <span>Login</span>
            </button>
            <button 
              onClick={() => {
                document.getElementById('dashboard-selection')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="flex items-center gap-2 px-8 py-3.5 md:px-10 md:py-4 text-sm md:text-base font-semibold rounded-xl border border-[var(--input-border)] bg-[var(--surface)] text-[var(--text)] hover:border-orange-300 hover:bg-[var(--accent-soft)] transition-all duration-200 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-orange-500/30"
            >
              View Features
            </button>
          </div>
        </div>
      </div>
      <canvas
        className="pointer-events-none absolute inset-0 mx-auto"
        id="canvas"
      ></canvas>
    </section>
  );
}
