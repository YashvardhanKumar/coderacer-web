// components/ProblemTable.tsx
import Link from 'next/link';
import Pagination from './pagination';
import useSWR from 'swr';
import { BASE_URL } from '@/lib/constants';
import { LoaderSmall } from './loader';

interface Problem {
    id: number;
    name: string;
    //   status?: 'solved' | 'attempted';
    //   hasSolution: boolean;
    //   acceptance: string;
    difficulty: 'EASY' | 'MEDIUM' | 'HARD';
}


const fetcher = (url: string) => fetch(url).then((r) => r.json())

export default function ProblemTable() {
    const { data, error, isLoading } = useSWR(`${BASE_URL}/api/problems/`, fetcher)

    if (isLoading) return <LoaderSmall />;

    if (error) return <div>Error: {error.message}</div>
    console.log(data);

    return (
        <div className="bg-white dark:bg-surface-dark border border-slate-200 dark:border-surface-border rounded-xl overflow-hidden shadow-sm dark:shadow-none">
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50 dark:bg-[#20252d] border-b border-slate-200 dark:border-surface-border text-xs uppercase text-slate-500 dark:text-text-secondary font-medium">
                        <tr>
                            <th className="px-6 py-4">Title</th>
                            <th className="px-6 py-4 w-32">Difficulty</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-surface-border text-sm">
                        {data?.results.map((problem: Problem, index: number) => (
                            <ProblemRow key={problem.id} problem={problem} index={index} />
                        ))}
                    </tbody>
                </table>
            </div>

            <Pagination />
        </div>
    );
}

// Problem Row Component
function ProblemRow({ problem, index }: { problem: Problem; index: number }) {
    const isEven = index % 2 === 1;

    const difficultyColors = {
        EASY: 'text-green-600 dark:text-green-500',
        MEDIUM: 'text-yellow-600 dark:text-yellow-500',
        HARD: 'text-red-600 dark:text-red-500'
    };

    const statusIcons = {
        solved: 'check_circle',
        attempted: 'hourglass_top'
    };

    const statusColors = {
        solved: 'text-green-500',
        attempted: 'text-yellow-500'
    };

    return (
        <tr
            className={`group hover:bg-slate-50 dark:hover:bg-[#222630] transition-colors ${isEven ? 'bg-slate-50/50 dark:bg-[#1e2129]' : ''
                }`}
        >
            <td className="px-6 py-4">
                <Link
                    href={`/problems/${problem.id}`}
                    className="font-medium text-slate-900 dark:text-white group-hover:text-primary transition-colors block"
                >
                    {problem.id}. {problem.name}
                </Link>
            </td>
            <td className="px-6 py-4">
                <span className={`font-medium ${difficultyColors[problem.difficulty]}`}>
                    {problem.difficulty}
                </span>
            </td>
        </tr>
    );
}