// components/Sidebar.tsx
import useSWR from 'swr';
import FilterAccordion from './filter-accordion';
import { BASE_URL } from '@/lib/constants';
import { Tag } from '@/lib/models';
import { LoaderSmall } from './loader';

export default function Sidebar() {
  const fetcher = (url: string) => fetch(url).then((r) => r.json())
  const { data: tags, isLoading } = useSWR(`${BASE_URL}/api/tags/`, fetcher)
  if (isLoading) return <LoaderSmall />;
  ;
  console.log(tags);

  return (
    <aside className="w-full lg:w-72 shrink-0 flex flex-col gap-6">
      {/* Filter Header for Mobile */}
      <div className="flex lg:hidden items-center justify-between">
        <h3 className="font-bold text-lg">Filters</h3>
        <button className="text-primary text-sm font-medium">Reset</button>
      </div>

      <div className="flex flex-col gap-3">
        {/* Status Accordion */}
        <FilterAccordion
          icon="task_alt"
          title="Status"
          defaultOpen
        >
          <div className="pb-3 pt-1 flex flex-col gap-2">
            <CheckboxItem label="Solved" />
            <CheckboxItem label="Unsolved" />
            <CheckboxItem label="Attempted" />
          </div>
        </FilterAccordion>

        {/* Difficulty Accordion */}
        <FilterAccordion
          icon="signal_cellular_alt"
          title="Difficulty"
          defaultOpen
        >
          <div className="pb-3 pt-1 flex flex-col gap-2">
            <CheckboxItem
              label="Easy"
              checkboxColor="checked:bg-green-500 checked:border-green-500"
              labelColor="text-green-600 dark:text-green-500"
            />
            <CheckboxItem
              label="Medium"
              checkboxColor="checked:bg-yellow-500 checked:border-yellow-500"
              labelColor="text-yellow-600 dark:text-yellow-500"
            />
            <CheckboxItem
              label="Hard"
              checkboxColor="checked:bg-red-500 checked:border-red-500"
              labelColor="text-red-600 dark:text-red-500"
            />
          </div>
        </FilterAccordion>

        {/* Tags Accordion */}
        <FilterAccordion
          icon="label"
          title="Tags"
        >
          <div className="pb-3 pt-2 flex flex-wrap gap-2">
            {tags.results.map((t: Tag) => (
              <span
                key={t.id}
                className="cursor-pointer px-2 py-1 bg-slate-100 dark:bg-slate-800 text-xs rounded text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                {t.tags}
              </span>
            ))}
          </div>
        </FilterAccordion>
      </div>

      {/* Company Tags Promo */}
      <div className="rounded-xl bg-linear-to-br from-primary/20 to-transparent p-4 border border-primary/20">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-primary">business_center</span>
          <div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
              Company Tags
            </h4>
            <p className="text-xs text-slate-500 dark:text-text-secondary mb-3">
              Unlock high-frequency problems from top companies.
            </p>
            <button className="text-xs bg-primary text-white px-3 py-1.5 rounded-lg font-medium hover:bg-primary/90">
              Get Premium
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}

// Checkbox Item Component
function CheckboxItem({
  label,
  checkboxColor = "checked:bg-primary checked:border-primary",
  labelColor = "text-slate-600 dark:text-text-secondary"
}: {
  label: string;
  checkboxColor?: string;
  labelColor?: string;
}) {
  return (
    <label className="flex items-center gap-3 cursor-pointer group/item">
      <div className="relative flex items-center">
        <input
          className={`peer size-4 appearance-none rounded border border-slate-300 dark:border-slate-600 bg-transparent transition-all ${checkboxColor}`}
          type="checkbox"
        />
        <span className="material-symbols-outlined absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white text-[12px] opacity-0 peer-checked:opacity-100 pointer-events-none">
          check
        </span>
      </div>
      <span className={`text-sm group-hover/item:text-primary transition-colors ${labelColor}`}>
        {label}
      </span>
    </label>
  );
}