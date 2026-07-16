'use client'

import { Skeleton } from '../ui/skeleton'
// components/problem/TestPanel.tsx

import { TestcaseList, Problem, User } from '@/lib/models'
import TestResultDetail from './test-result-detail'

interface Props {
  problem: Problem
  user: User | null
  language: string
  runData: any[] | null
  submitData: any[] | null
  isLoading: boolean
  error: string | null
  activeTab: string
  setActiveTab: (tab: string) => void
  activeCase: number
  setActiveCase: (index: number) => void
  sampleTestcases: TestcaseList[]
  setSampleTestcases: React.Dispatch<React.SetStateAction<TestcaseList[]>>
}

export default function TestPanel({
  problem,
  user,
  language,
  runData,
  submitData,
  isLoading,
  error,
  activeTab,
  setActiveTab,
  activeCase,
  setActiveCase,
  sampleTestcases,
  setSampleTestcases,
}: Props) {
  const autoResize = (el: HTMLTextAreaElement | null) => {
    if (el) {
      el.style.height = 'auto'
      el.style.height = el.scrollHeight + 'px'
      if (!(el as any)._resizeObs) {
        const ro = new ResizeObserver(() => {
          el.style.height = 'auto'
          el.style.height = el.scrollHeight + 'px'
        })
        ro.observe(el)
        ;(el as any)._resizeObs = ro
      }
    }
  }

  const handleInputChange = (lineIndex: number, newValue: string) => {
    setSampleTestcases((prev) => {
      const updated = [...prev]
      const currentCase = { ...updated[activeCase] }
      if (currentCase) {
        const lines = currentCase.input.replaceAll('\r\n', '\n').split('\n')
        if (problem.is_multi) {
          lines[lineIndex] = newValue
        } else {
          const line = lines[lineIndex]
          const splitIdx = line.indexOf('=')
          if (splitIdx !== -1) {
            const key = line.substring(0, splitIdx).trim()
            lines[lineIndex] = `${key} = ${newValue}`
          } else {
            lines[lineIndex] = newValue
          }
        }
        currentCase.input = lines.join('\n')
        updated[activeCase] = currentCase
      }
      return updated
    })
  }

  const handleDeleteTestcase = (indexToDelete: number) => {
    const updated = sampleTestcases.filter((_, idx) => idx !== indexToDelete)
    setSampleTestcases(updated)
    if (activeCase >= updated.length) {
      setActiveCase(Math.max(0, updated.length - 1))
    } else if (activeCase === indexToDelete && activeCase > 0) {
      setActiveCase(activeCase - 1)
    }
  }

  const handleAddTestcase = () => {
    let newInput = problem.is_multi ? '[]\n[]' : ''
    if (sampleTestcases.length > 0 && !problem.is_multi) {
      const lines = sampleTestcases[0].input
        .replaceAll('\r\n', '\n')
        .split('\n')
      const newLines = lines.map((line) => {
        const splitIdx = line.indexOf('=')
        if (splitIdx !== -1) {
          const key = line.substring(0, splitIdx).trim()
          return `${key} = `
        }
        return ''
      })
      newInput = newLines.join('\n')
    }

    const newCase = {
      id: Math.max(0, ...sampleTestcases.map((t) => t.id || 0)) + 1,
      input: newInput,
      output: '',
      display_testcase: true,
      created_at: new Date().toISOString(),
    }

    setSampleTestcases([...sampleTestcases, newCase])
    setActiveCase(sampleTestcases.length)
  }

  const getTabStatusClasses = (index: number, isSubmit?: boolean) => {
    const result = isSubmit ? submitData?.[index] : runData?.[index]
    const isActive = activeCase === index

    if (result) {
      const isAccepted = result.status?.id === 3
      if (result.status === null) {
        return isActive
          ? 'bg-gray-600/20 text-gray-500 border-gray-500/50'
          : 'bg-gray-400 text-gray-500 hover:bg-gray-600/10 border-transparent'
      } else if (isAccepted) {
        return isActive
          ? 'bg-green-600/20 text-green-500 border-green-500/50'
          : 'text-green-500 hover:bg-green-600/10 border-transparent'
      } else {
        return isActive
          ? 'bg-red-600/20 text-red-500 border-red-500/50'
          : 'text-red-500 hover:bg-red-600/10 border-transparent'
      }
    }

    return isActive
      ? 'bg-surface-border text-white border-surface-border'
      : 'text-gray-400 hover:text-white hover:bg-surface-border border-transparent'
  }

  return (
    <div className="h-full border-t border-surface-border bg-surface-dark flex flex-col shrink-0">
      {/* Panel Header */}
      <div className="flex items-center px-4 py-2 gap-4 border-b border-surface-border bg-black/20">
        <button
          onClick={() => setActiveTab('testcase')}
          className={`flex items-center gap-2 text-xs font-bold border-b-2 pb-2 transition-all ${
            activeTab === 'testcase'
              ? 'text-white border-primary'
              : 'text-gray-500 hover:text-white border-transparent'
          }`}
        >
          Testcase
        </button>
        <button
          onClick={() => setActiveTab('result')}
          className={`flex items-center gap-2 text-xs font-bold border-b-2 pb-2 transition-all ${
            activeTab === 'result'
              ? 'text-white border-primary'
              : 'text-gray-500 hover:text-white border-transparent'
          }`}
        >
          Test Result
        </button>
        <button
          onClick={() => setActiveTab('submission')}
          className={`flex items-center gap-2 text-xs font-bold border-b-2 pb-2 transition-all ${
            activeTab === 'submission'
              ? 'text-white border-primary'
              : 'text-gray-500 hover:text-white border-transparent'
          }`}
        >
          Code Submission
        </button>
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-hidden px-4 flex flex-col">
        {activeTab === 'testcase' && (
          <div
            key="testcase-tab"
            className="animate-in fade-in duration-200 flex-1 overflow-y-auto min-h-0 py-2 pr-1"
          >
            <div className="flex gap-2 mb-4 mt-2">
              {sampleTestcases.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setActiveCase(index)}
                  className={`relative px-4 py-1.5 rounded-md text-xs font-medium transition-all active:scale-95 border ${
                    activeCase === index
                      ? 'bg-surface-border text-white border-surface-border'
                      : 'text-gray-400 hover:text-white hover:bg-surface-border border-transparent'
                  }`}
                >
                  Case {index + 1}
                  {sampleTestcases.length > 1 && activeCase === index && (
                    <span
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteTestcase(index)
                      }}
                      className="absolute -top-1 -right-1 bg-neutral-800 hover:bg-neutral-700 text-gray-400 hover:text-white rounded-full size-3.5 flex items-center justify-center text-[10px] transition-colors cursor-pointer font-bold border border-neutral-700/50 shadow-sm"
                      title="Delete Case"
                    >
                      ×
                    </span>
                  )}
                </button>
              ))}

              <button
                onClick={handleAddTestcase}
                title="Add Testcase"
                className="text-gray-400 hover:text-white hover:bg-surface-border size-7 flex items-center justify-center rounded-md transition-all active:scale-90"
              >
                <span className="material-symbols-outlined text-lg">add</span>
              </button>
            </div>

            <div
              key={activeCase}
              className="space-y-3 font-mono text-xs animate-in fade-in duration-200"
            >
              {sampleTestcases && sampleTestcases[activeCase]?.input ? (
                problem.is_multi ? (
                  sampleTestcases[activeCase].input
                    .replaceAll('\r\n', '\n')
                    .split('\n')
                    .map((line, i) => (
                      <div key={i}>
                        <p className="text-gray-400 mb-1">
                          {i === 0 ? 'Method calls' : 'Arguments'}
                        </p>
                        <textarea
                          value={line}
                          onChange={(e) => handleInputChange(i, e.target.value)}
                          rows={1}
                          className="w-full bg-surface-border px-3 py-2 rounded text-white border border-gray-700 outline-none focus:border-primary focus:ring-1 focus:ring-primary font-mono text-xs resize-none overflow-hidden whitespace-pre-wrap"
                          onInput={(e) => autoResize(e.currentTarget)}
                          ref={autoResize}
                        />
                      </div>
                    ))
                ) : (
                  sampleTestcases[activeCase].input
                    .replaceAll('\r\n', '\n')
                    .split('\n')
                    .map((line, i) => {
                      const splitIdx = line.indexOf('=')
                      if (splitIdx !== -1) {
                        const key = line.substring(0, splitIdx).trim()
                        const value = line.substring(splitIdx + 1).trim()
                        return (
                          <div key={i}>
                            <p className="text-gray-400 mb-1">{key} = </p>
                            <textarea
                              value={value}
                              onChange={(e) =>
                                handleInputChange(i, e.target.value)
                              }
                              rows={1}
                              className="w-full bg-surface-border px-3 py-2 rounded text-white border border-gray-700 outline-none focus:border-primary focus:ring-1 focus:ring-primary font-mono text-xs resize-none overflow-hidden whitespace-pre-wrap"
                              onInput={(e) => autoResize(e.currentTarget)}
                              ref={autoResize}
                            />
                          </div>
                        )
                      } else {
                        return (
                          <div key={i}>
                            <p className="text-gray-400 mb-1">
                              {problem.variables && problem.variables[i]
                                ? problem.variables[i].name
                                : `Arg ${i + 1}`}{' '}
                              ={' '}
                            </p>
                            <textarea
                              value={line}
                              onChange={(e) =>
                                handleInputChange(i, e.target.value)
                              }
                              rows={1}
                              className="w-full bg-surface-border px-3 py-2 rounded text-white border border-gray-700 outline-none focus:border-primary focus:ring-1 focus:ring-primary font-mono text-xs resize-none overflow-hidden whitespace-pre-wrap"
                              onInput={(e) => autoResize(e.currentTarget)}
                              ref={autoResize}
                            />
                          </div>
                        )
                      }
                    })
                )
              ) : (
                <div className="text-gray-500 italic p-2">Hidden test case</div>
              )}
            </div>
          </div>
        )}
        {activeTab === 'result' && (
          <div
            key="result-tab"
            className="text-gray-400 text-sm animate-in fade-in duration-200 flex-1 overflow-y-auto min-h-0 py-2 pr-1"
          >
            {isLoading ? (
              <div className="space-y-4 py-4 animate-in fade-in duration-300">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-widest opacity-70 animate-pulse">
                    compiling code...
                  </span>
                </div>
                <div className="space-y-3">
                  <Skeleton className="h-5 w-32 rounded" />
                  <div className="flex gap-2">
                    <Skeleton className="h-8 w-20 rounded-md" />
                    <Skeleton className="h-8 w-20 rounded-md" />
                    <Skeleton className="h-8 w-20 rounded-md" />
                  </div>
                  <div className="space-y-2 mt-4">
                    <Skeleton className="h-4 w-full rounded" />
                    <Skeleton className="h-4 w-full rounded" />
                    <Skeleton className="h-4 w-2/3 rounded" />
                  </div>
                </div>
              </div>
            ) : error ? (
              <div className="py-4">
                <div className="text-red-500 font-bold mb-2 flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">
                    error
                  </span>
                  Error
                </div>
                <pre className="bg-surface-border p-3 rounded text-red-400 border border-red-900/50 font-mono text-xs whitespace-pre-wrap">
                  {error}
                </pre>
              </div>
            ) : runData && runData[activeCase] ? (
              <div
                key={activeCase}
                className="space-y-3 pb-3 animate-in fade-in duration-200"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`font-bold ${runData[activeCase]?.status?.id === 3 ? 'text-green-500' : 'text-red-500'}`}
                  >
                    {runData[activeCase]?.status?.description}
                  </div>
                  {runData[activeCase]?.user_time_ms !== undefined && (
                    <span className="text-xs font-mono text-gray-400">
                      · {Math.round(runData[activeCase].user_time_ms)} ms
                    </span>
                  )}
                </div>
                <div className="flex gap-2 mb-4 mt-2">
                  {sampleTestcases.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setActiveCase(index)}
                      className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all active:scale-95 border ${getTabStatusClasses(index)}`}
                    >
                      Case {index + 1}
                    </button>
                  ))}
                </div>

                <TestResultDetail
                  result={runData[activeCase]}
                  testcase={sampleTestcases[activeCase]}
                  variables={problem.variables}
                />
              </div>
            ) : (
              <div className="py-4 italic">Run code first to show</div>
            )}
          </div>
        )}

        {activeTab === 'submission' && (
          <div className="text-gray-400 text-sm animate-in fade-in slide-in-from-bottom-2 duration-300 flex-1 flex flex-col min-h-0 py-2">
            {submitData ? (
              <div className="flex divide-x relative space-x-3 flex-1 min-h-0">
                <div
                  className={`overflow-y-auto gap-3 pr-3 content-start items-start ${isLoading ? 'flex flex-wrap' : 'grid grid-cols-1 shrink-0'}`}
                >
                  {submitData.map((res, index) => (
                    <button
                      key={index}
                      onClick={() => setActiveCase(index)}
                      className={`px-3 py-1.5 rounded-md w-24 h-fit flex justify-start gap-1 text-xs font-medium transition-all active:scale-95 border ${submitData[index]?.status?.id === 1 ? '' : getTabStatusClasses(index, true)}`}
                    >
                      {submitData[index]?.status?.id === 1 && (
                        <div className="animate-spin size-3 border border-primary border-t-transparent rounded-full"></div>
                      )}
                      <span>Case {index + 1}</span>
                    </button>
                  ))}
                </div>
                {!isLoading && (
                  <div className="flex-1 overflow-y-auto h-full pl-3 pr-1">
                    {!isLoading ? (
                      <TestResultDetail
                        result={submitData[activeCase]}
                        testcase={sampleTestcases[activeCase]}
                        variables={problem.variables}
                      />
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center gap-4 text-gray-500">
                        <div className="animate-spin size-8 border-4 border-primary border-t-transparent rounded-full"></div>
                        <p className="text-xs font-bold uppercase tracking-widest">
                          Processing Submission...
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-20 flex flex-col items-center justify-center gap-4 text-gray-600">
                <span className="material-symbols-outlined text-4xl opacity-20">
                  publish
                </span>
                <p className="text-xs font-bold uppercase tracking-widest opacity-50">
                  Submit code for full evaluation
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
