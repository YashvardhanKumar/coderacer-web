// components/shared/DifficultyBadge.tsx
interface DifficultyBadgeProps {
  difficulty: 'Easy' | 'Medium' | 'Hard';
}

export default function DifficultyBadge({ difficulty }: DifficultyBadgeProps) {
  const styles = {
    Easy: 'bg-emerald-500/10 text-emerald-400',
    Medium: 'bg-yellow-500/10 text-yellow-400',
    Hard: 'bg-red-500/10 text-red-400'
  };

  return (
    <span className={`px-2.5 py-0.5 rounded-full ${styles[difficulty]} text-xs font-medium`}>
      {difficulty}
    </span>
  );
}