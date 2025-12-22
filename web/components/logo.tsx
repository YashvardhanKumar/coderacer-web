// components/shared/Logo.tsx
import Link from 'next/link';

interface LogoProps {
  variant?: 'default' | 'problem';
}

export default function Logo({ variant = 'default' }: LogoProps) {
  const iconColor = variant === 'problem' ? 'text-orange-400' : 'text-primary';
  const textColor = variant === 'problem' ? 'text-white' : 'text-slate-900 dark:text-white';

  return (
    <Link href="/" className={`flex items-center gap-2 ${textColor} cursor-pointer`}>
      <div className={`size-6`}>
        <div className={`font-bold text-cyan-400`}>
          {'</>'}
        </div>
      </div>
      <h2 className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500"
        style={{ animationDuration: '2s' }}>
        Coderacer
      </h2>
      {/* <h2 className={`${textColor} ${variant === 'problem' ? 'text-base' : 'text-lg'} font-bold leading-tight tracking-[-0.015em] hidden sm:block`}>
        Coderacer
      </h2> */}
    </Link>
  );
}