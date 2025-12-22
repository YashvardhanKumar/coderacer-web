// components/problem/TestPanel.tsx
'use client';

import { useState } from 'react';

export default function TestPanel() {
  const [activeTab, setActiveTab] = useState('testcase');
  const [activeCase, setActiveCase] = useState(1);

  return (
    <div className="h-full border-t border-[#282e39] bg-[#1a1a1a] flex flex-col shrink-0">
      {/* Panel Header */}
      <div className="flex items-center px-4 py-2 gap-4">
        <button
          onClick={() => setActiveTab('testcase')}
          className={`flex items-center gap-2 text-xs font-bold border-b-2 pb-2 transition-colors ${
            activeTab === 'testcase'
              ? 'text-white border-primary'
              : 'text-gray-500 hover:text-white border-transparent'
          }`}
        >
          <span className="material-symbols-outlined text-[16px] text-green-500">check_circle</span>
          Testcase
        </button>
        <button
          onClick={() => setActiveTab('result')}
          className={`flex items-center gap-2 text-xs font-bold border-b-2 pb-2 transition-colors ${
            activeTab === 'result'
              ? 'text-white border-primary'
              : 'text-gray-500 hover:text-white border-transparent'
          }`}
        >
          Test Result
        </button>
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-14">
        {activeTab === 'testcase' && (
          <>
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setActiveCase(1)}
                className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  activeCase === 1
                    ? 'bg-[#282e39] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-[#282e39]'
                }`}
              >
                Case 1
              </button>
              <button
                onClick={() => setActiveCase(2)}
                className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  activeCase === 2
                    ? 'bg-[#282e39] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-[#282e39]'
                }`}
              >
                Case 2
              </button>
              <button
                onClick={() => setActiveCase(3)}
                className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  activeCase === 3
                    ? 'bg-[#282e39] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-[#282e39]'
                }`}
              >
                Case 3
              </button>
              <button className="text-gray-400 hover:text-white hover:bg-[#282e39] size-7 flex items-center justify-center rounded-md transition-colors">
                <span className="material-symbols-outlined text-[18px]">add</span>
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <p className="text-gray-400 mb-1">nums =</p>
                <div className="bg-[#282e39] p-2 rounded text-white border border-gray-700">
                  [2,7,11,15]
                </div>
              </div>
              <div>
                <p className="text-gray-400 mb-1">target =</p>
                <div className="bg-[#282e39] p-2 rounded text-white border border-gray-700">
                  9
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'result' && (
          <div className="text-gray-400 text-sm">
            Run your code to see test results here
          </div>
        )}
      </div>

      {/* Run/Submit Footer */}
      <div className="absolute bottom-0 w-full p-2 flex justify-between items-center bg-[#1a1a1a] border-t border-surface-border">
        <button className="text-gray-400 hover:text-white text-xs px-3 py-1.5 rounded hover:bg-[#282e39] flex items-center gap-2 transition-colors">
          <span className="material-symbols-outlined text-[18px]">terminal</span>
          Console
        </button>
        <div className="flex gap-2">
          <button className="btn-primary">
            Run
          </button>
          <button className="btn-secondary">
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}