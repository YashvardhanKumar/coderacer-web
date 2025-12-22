// components/shared/TabButton.tsx
interface TabButtonProps {
  icon: string;
  label: string;
  active?: boolean;
  onClick?: () => void;
}

export default function TabButton({ icon, label, active = false, onClick }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-3 h-full border-b-2 text-xs font-medium rounded-t-sm transition-colors ${
        active
          ? 'border-primary text-white bg-[#282e39]'
          : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-[#282e39]/50'
      }`}
    >
      <span className={`material-symbols-outlined text-[16px] ${active ? 'text-primary' : ''}`}>
        {icon}
      </span>
      {label}
    </button>
  );
}