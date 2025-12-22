// components/problem/ProblemDescription.tsx
'use client';

import { useState } from 'react';
import TabButton from '@/components/tab-button';
import DifficultyBadge from '@/components/difficulty-badge';
import CodeBlock from '@/components/code-block';
import { ResizablePanel } from '../ui/resizable';
import { Problem } from '@/lib/models';

const tabs = [
  { id: 'description', label: 'Description', icon: 'description' },
  { id: 'editorial', label: 'Editorial', icon: 'edit_note' },
  { id: 'solutions', label: 'Solutions', icon: 'science' },
  { id: 'submissions', label: 'Submissions', icon: 'history' }
];

interface Props {
  problem: Problem
}

export default function ProblemDescription({ problem }: Props) {
  const [activeTab, setActiveTab] = useState('description');

  return (
    <ResizablePanel defaultSize={50} className="flex flex-col border-r border-[#282e39] bg-background-dark overflow-hidden relative">
      {/* Tabs Header */}
      <div className="h-10 bg-[#1a1a1a] flex items-center px-2 gap-1 border-b border-[#282e39] shrink-0">
        {tabs.map(tab => (
          <TabButton
            key={tab.id}
            icon={tab.icon}
            label={tab.label}
            active={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          />
        ))}
      </div>

      {/* Content Scroll Area */}
      <div className="flex-1 overflow-y-auto p-5 pb-20">
        {activeTab === 'description' && <DescriptionContent problem={problem} />}
        {activeTab === 'editorial' && <div className="text-gray-400">Editorial content...</div>}
        {activeTab === 'solutions' && <div className="text-gray-400">Solutions content...</div>}
        {activeTab === 'submissions' && <div className="text-gray-400">Submissions content...</div>}
      </div>

      {/* Footer */}
      <div className="absolute bottom-0 w-full h-10 bg-[#1a1a1a] border-t border-[#282e39] flex items-center justify-between px-4 z-10">
        <button className="text-gray-400 hover:text-white text-xs flex items-center gap-1">
          <span className="material-symbols-outlined text-[16px]">forum</span>
          Discussion (32)
        </button>
        <span className="text-xs text-gray-600">Copyright © 2025 Coderacer</span>
      </div>
    </ResizablePanel>
  );
}

function DescriptionContent({ problem }: Props) {
  return (
    <>
      {/* Title & Header */}
      <div className="flex justify-between items-start mb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight">1. Two Sum</h1>
        <div className="flex gap-2">
          <a href="#" className="text-gray-500 hover:text-white transition-colors">
            <span className="material-symbols-outlined text-[20px]">help</span>
          </a>
        </div>
      </div>

      {/* Chips */}
      <div className="flex gap-2 mb-4 flex-wrap items-center">
        <DifficultyBadge difficulty="Easy" />
        <div className="h-5 w-px bg-gray-700" />
        <button className="flex items-center gap-1 bg-[#282e39] hover:bg-[#323844] px-2 py-0.5 rounded-full text-xs text-gray-300 transition-colors">
          <span className="material-symbols-outlined text-[14px]">sell</span>
          Topics
        </button>
        <button className="flex items-center gap-1 bg-[#282e39] hover:bg-[#323844] px-2 py-0.5 rounded-full text-xs text-gray-300 transition-colors">
          <span className="material-symbols-outlined text-[14px]">lock</span>
          Companies
        </button>
      </div>

      {/* Problem Text */}
      <div className="text-sm text-gray-300 leading-relaxed space-y-4">
        <p>
          Given an array of integers <CodeBlock inline>nums</CodeBlock> and an integer{' '}
          <CodeBlock inline>target</CodeBlock>, return indices of the two numbers such that they add up to{' '}
          <CodeBlock inline>target</CodeBlock>.
        </p>
        <p>
          You may assume that each input would have <strong>exactly one solution</strong>, and you may not use the same element twice.
        </p>
        <p>You can return the answer in any order.</p>

        <div dangerouslySetInnerHTML={{ __html: problem?.problem_description ?? '' }}></div>

        <div className="mt-12 border-t border-[#282e39] pt-6 flex flex-wrap gap-4">
          <div className="flex items-center gap-1 cursor-pointer group">
            <span className="material-symbols-outlined text-gray-500 group-hover:text-green-500 transition-colors text-[20px]">thumb_up</span>
            <span className="text-gray-500 text-xs font-bold group-hover:text-white">24.5K</span>
          </div>
          <div className="flex items-center gap-1 cursor-pointer group">
            <span className="material-symbols-outlined text-gray-500 group-hover:text-red-500 transition-colors text-[20px]">thumb_down</span>
            <span className="text-gray-500 text-xs font-bold group-hover:text-white">1.2K</span>
          </div>
          <div className="flex items-center gap-1 cursor-pointer group ml-auto">
            <span className="material-symbols-outlined text-gray-500 group-hover:text-yellow-400 transition-colors text-[20px]">star</span>
            <span className="text-gray-500 text-xs font-bold group-hover:text-white">Add to List</span>
          </div>
          <div className="flex items-center gap-1 cursor-pointer group">
            <span className="material-symbols-outlined text-gray-500 group-hover:text-blue-400 transition-colors text-[20px]">share</span>
            <span className="text-gray-500 text-xs font-bold group-hover:text-white">Share</span>
          </div>
        </div>
      </div>
    </>
  );
}