// components/DailyChallenge.tsx
import Link from 'next/link';

export default function DailyChallenge() {
  return (
    <Link
      href="/problems/daily"
      className="relative overflow-hidden rounded-xl border border-slate-200 dark:border-surface-border bg-white dark:bg-surface-dark shadow-sm dark:shadow-[0_0_15px_rgba(0,0,0,0.2)] group cursor-pointer hover:border-primary/50 transition-colors"
    >
      <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
        <span className="material-symbols-outlined text-6xl">emoji_events</span>
      </div>
      
      <div className="p-4 flex flex-col h-full justify-between gap-3 relative z-10">
        <div>
          <div className="flex justify-between items-start mb-1">
            <p className="text-slate-500 dark:text-text-secondary text-xs font-semibold uppercase tracking-wider">
              Daily Challenge
            </p>
            <span className="bg-primary/10 text-primary text-[10px] font-bold px-2 py-0.5 rounded-full">
              APR 12
            </span>
          </div>
          <h3 className="text-slate-900 dark:text-white text-lg font-bold leading-tight line-clamp-1 group-hover:text-primary transition-colors">
            Invert Binary Tree
          </h3>
        </div>
        
        <div className="flex items-center justify-between mt-1">
          <div className="flex -space-x-2">
            <div className="w-6 h-6 rounded-full border-2 border-white dark:border-surface-dark bg-slate-200 dark:bg-slate-700" />
            <div className="w-6 h-6 rounded-full border-2 border-white dark:border-surface-dark bg-slate-300 dark:bg-slate-600" />
            <div className="w-6 h-6 rounded-full border-2 border-white dark:border-surface-dark bg-slate-400 dark:bg-slate-500 flex items-center justify-center text-[8px] font-bold text-white">
              +99
            </div>
          </div>
          <button className="text-primary text-xs font-bold hover:underline">
            Solve Now →
          </button>
        </div>
      </div>
    </Link>
  );
}