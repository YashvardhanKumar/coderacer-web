// components/problem/EditorToolbar.tsx
'use client';

import IconButton from '@/components/icon-button';

export default function EditorToolbar() {
  return (
    <div className="h-10 bg-[#1a1a1a] flex items-center justify-between px-2 border-b border-[#282e39] shrink-0">
      <div className="flex items-center gap-2">
        <div className="relative group">
          <button className="flex items-center gap-2 text-green-400 text-xs font-medium hover:bg-[#282e39] px-2 py-1 rounded transition-colors">
            <span>C++</span>
            <span className="material-symbols-outlined text-[16px]">keyboard_arrow_down</span>
          </button>
        </div>
        
        <div className="h-4 w-px bg-gray-700" />
        
        <button className="flex items-center gap-2 text-gray-400 text-xs font-medium hover:bg-[#282e39] hover:text-white px-2 py-1 rounded transition-colors">
          Auto
        </button>
      </div>

      <div className="flex items-center gap-1">
        <IconButton icon="settings" title="Settings" variant="toolbar" />
        <IconButton icon="keyboard" title="Shortcut keys" variant="toolbar" />
        <IconButton icon="history" title="Restore default code" variant="toolbar" />
        <IconButton icon="fullscreen" title="Expand" variant="toolbar" />
      </div>
    </div>
  );
}