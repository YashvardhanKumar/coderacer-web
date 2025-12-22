// components/problem/ProblemHeader.tsx
import Link from 'next/link';
import Logo from '@/components/logo';
import IconButton from '@/components/icon-button';

export default function ProblemHeader() {
  return (
    <header className="h-12.5 shrink-0 flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#282e39] bg-[#1a1a1a] px-4">
      <div className="flex items-center gap-6">
        <Logo variant="problem" />
        
        <div className="h-4 w-px bg-gray-600 mx-2 hidden md:block" />
        
        <div className="flex items-center gap-4">
          <Link href="/problems" className="flex items-center gap-1 text-gray-300 hover:text-white text-sm font-medium">
            <span className="material-symbols-outlined text-[18px]">list</span>
            Problem List
          </Link>
          
          <div className="flex items-center gap-1 text-gray-400 text-sm">
            <IconButton icon="chevron_left" title="Previous Problem" />
            <IconButton icon="chevron_right" title="Next Problem" />
            <IconButton icon="shuffle" title="Random Problem" />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="bg-[#282828] hover:bg-[#323232] text-gray-300 px-3 py-1.5 rounded text-xs font-medium flex items-center gap-2 transition-colors">
          <span className="material-symbols-outlined text-[16px] text-yellow-500">bug_report</span>
          Debug
        </button>
        
        <button className="flex items-center justify-center overflow-hidden rounded-md bg-primary/20 hover:bg-primary/30 transition-colors h-8 px-3 text-primary text-xs font-bold">
          Premium
        </button>
        
        <div className="flex items-center gap-3">
          <button className="text-gray-400 hover:text-white relative">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            <span className="absolute top-0 right-0 size-2 bg-red-500 rounded-full" />
          </button>
          
          <div
            className="bg-center bg-no-repeat bg-cover rounded-full size-7 cursor-pointer border border-gray-600"
            style={{
              backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBvv9YVwwDpVlRZWQTOkT3G5121GnaiCW5cjxYWtRv17gYpzz39qrjMYh41j8575cBKpM8sofVT7E09AtYRQLyUYoZdtkWMnqxwRaEXbDfVTR7UpO97NQy5BoxDts6eb4wJDleKzsSXD96b9UV9PvzorjAUeXGC_d4hP2Glg66kNeWquJMGwnqkOuqiGcpjjSElg-7eEF6BrvKZDs4KZW43eJ-e7v50mYoE58K1uiFJBiRhDJrqJVvlAQmudFZOhaEiwJqFhcWhd5cN")'
            }}
          />
        </div>
      </div>
    </header>
  );
}