// components/FilterAccordion.tsx
'use client';

import { ReactNode } from 'react';

interface FilterAccordionProps {
  icon: string;
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

export default function FilterAccordion({
  icon,
  title,
  children,
  defaultOpen = false
}: FilterAccordionProps) {
  return (
    <details
      className="flex flex-col rounded-xl border border-slate-200 dark:border-surface-border bg-white dark:bg-surface-dark px-4 py-2 group shadow-sm dark:shadow-none"
      open={defaultOpen}
    >
      <summary className="flex cursor-pointer items-center justify-between py-2 list-none">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-slate-400 dark:text-text-secondary">
            {icon}
          </span>
          <p className="text-slate-900 dark:text-white text-sm font-medium">
            {title}
          </p>
        </div>
        <span className="material-symbols-outlined text-slate-400 dark:text-text-secondary group-open:rotate-180 transition-transform">
          expand_more
        </span>
      </summary>
      {children}
    </details>
  );
}