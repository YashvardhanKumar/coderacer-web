'use client'

import EditorToolbar from './editor-toolbar'
import TestPanel from './test-panel'
import Editor from '@monaco-editor/react'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '../ui/resizable'
import {
  Language,
  LanguageCodes,
  Problem,
  User,
  TestcaseList,
} from '@/lib/models'
import { useEffect, useState, useRef } from 'react'
import { ImperativePanelHandle } from 'react-resizable-panels'
import apiClient, { apiFetch } from '@/lib/utils'
import { toast } from 'sonner'
import { mutate } from 'swr'
import Link from 'next/link'
import { Button } from '../ui/button'
import SubmissionResult from './submission-result'
import { AnimatePresence } from 'framer-motion'
import { useMemo } from 'react'
import { PaginatedResponse, Solution, Status } from '@/lib/models'
import { apiFetcher } from '@/lib/utils'
import useSWR from 'swr'

interface Props {
  problem: Problem
  user: User | null
  maximizedSide?: 'left' | 'right' | null
  onMaximize?: () => void
  onRestore?: () => void
  ref?: React.Ref<ImperativePanelHandle>
  isContestMode?: boolean
  contestId?: number
}

function CodeEditor({
  problem,
  user,
  maximizedSide,
  onMaximize,
  onRestore,
  ref,
  isContestMode = false,
  contestId,
}: Props) {
  const [language, setLanguage] = useState<Language>(
    user?.default_lang ?? Language.CPP
  )
  const [code, setCode] = useState<string | null>(null)
  const [runData, setRunData] = useState<any[] | null>(null)
  const [submitData, setSubmitData] = useState<any[] | null>(null)
  const [finalSubmission, setFinalSubmission] = useState<Solution | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('testcase')
  const [activeCase, setActiveCase] = useState(0)
  const [isTestPanelCollapsed, setIsTestPanelCollapsed] = useState(false)
  const [sampleTestcases, setSampleTestcases] = useState<TestcaseList[]>([])

  const { data: submissionsData } = useSWR<
    PaginatedResponse<Solution> | Solution[]
  >(user ? `solutions/?problem_id=${problem.id}` : null, apiFetcher)

  const history = useMemo(() => {
    const subs = Array.isArray(submissionsData)
      ? submissionsData
      : submissionsData?.results || []
    return subs.filter((s) => s.status === Status.SUCCESS && s.testcase_results)
  }, [submissionsData])

  const testPanelRef = useRef<ImperativePanelHandle>(null)

  const availableLanguages = problem.codeblocks?.map((cb) => cb.language) ?? []

  useEffect(() => {
    if (problem && problem.testcases) {
      setSampleTestcases(
        problem.testcases.filter((e) => e.display_testcase == true)
      )
    }
  }, [problem])

  // Update default language in backend whenever it changes
  useEffect(() => {
    if (user && language !== user.default_lang) {
      apiClient
        .patch('auth/users/update_language/', { default_lang: language })
        .catch((err) => console.error('Failed to update default language', err))
    }
  }, [language, user])

  useEffect(() => {
    if (!problem.id) return

    const storageKey = `code-racer-${problem.id}-${language}`
    const savedCode = localStorage.getItem(storageKey)

    if (savedCode !== null) {
      setCode(savedCode)
    } else {
      const defaultCode =
        problem.codeblocks?.find((e) => e.language === language)?.block ?? ''
      setCode(defaultCode)
    }
  }, [problem.id, language, problem.codeblocks])

  useEffect(() => {
    if (code === null || !problem.id) return
    const storageKey = `code-racer-${problem.id}-${language}`
    localStorage.setItem(storageKey, code)
  }, [code, problem.id, language])

  const handleReset = () => {
    const storageKey = `code-racer-${problem.id}-${language}`
    localStorage.removeItem(storageKey)
    const defaultCode =
      problem.codeblocks?.find((e) => e.language === language)?.block ?? ''
    setCode(defaultCode)
  }

  const handleEditorDidMount = (editor: any, monaco: any) => {
    if (monaco) {
      monaco.languages.typescript.typescriptDefaults.setDiagnosticsOptions({
        noSemanticValidation: true,
        noSyntaxValidation: true,
      })
      monaco.languages.typescript.javascriptDefaults.setDiagnosticsOptions({
        noSemanticValidation: true,
        noSyntaxValidation: true,
      })
    }
  }

  const toggleTestPanel = () => {
    const panel = testPanelRef.current
    if (panel) {
      if (isTestPanelCollapsed) {
        try {
          const saved = localStorage.getItem(
            'react-resizable-panels:coderacer-vertical-layout'
          )
          if (saved) {
            const sizes = JSON.parse(saved)
            if (Array.isArray(sizes) && sizes.length === 2) {
              panel.expand()
              panel.resize(sizes[1])
              return
            }
          }
        } catch (e) {
          console.error('Error expanding vertical layout:', e)
        }
        panel.expand(40)
      } else {
        panel.collapse()
      }
    }
  }

  const handleMaximize = () => {
    if (onMaximize) {
      onMaximize()
    }
    if (testPanelRef.current) {
      testPanelRef.current.collapse()
    }
  }

  const runCode = async () => {
    setIsLoading(true)
    setActiveTab('result')
    setError(null)

    const relevantTestcases = sampleTestcases

    const initialRunData = relevantTestcases.map(() => ({
      status: { id: 1, description: 'Running' },
    }))
    setRunData(initialRunData)
    setActiveCase(0)

    if (isTestPanelCollapsed) {
      testPanelRef.current?.expand()
    }

    try {
      const runUrl = contestId
        ? `engine/submit-stream/?mode=run&contest_id=${contestId}`
        : 'engine/submit-stream/?mode=run'
      const response = await apiFetch(runUrl, {
        method: 'POST',
        body: JSON.stringify({
          problem_id: problem.id,
          source_code: code,
          language: language,
          language_id: LanguageCodes[language],
          contest_id: contestId,
          custom_testcases: sampleTestcases.map((tc) => ({
            id: tc.id,
            input: tc.input,
            output: tc.output || '',
            display_testcase: tc.display_testcase,
          })),
        }),
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Stream reader not available')

      const decoder = new TextDecoder()
      let currentResults = [...initialRunData]
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const payload = JSON.parse(line)
            if (payload.status === 'case_result') {
              const res = payload.data
              currentResults[res.index] = res
              setRunData([...currentResults])
            } else if (payload.status === 'complete') {
              setIsLoading(false)
              if (payload.compile_output) {
                setError(payload.compile_output)
              }
            } else if (payload.status === 'error') {
              setError(payload.message)
              setIsLoading(false)
            }
          } catch (e) {
            console.error('JSON parse error on line:', line, e)
          }
        }
      }
    } catch (err: any) {
      console.error('Error running code:', err)
      setError(err.message || 'Failed to run code')
      setIsLoading(false)
    }
  }

  const submitCode = async () => {
    const token = localStorage.getItem('token')
    if (!user || !token) {
      toast.error('Please sign in to submit code')
      return
    }

    setIsLoading(true)
    setActiveTab('submission')
    setError(null)

    const allTestcases = [...problem.testcases].sort((a, b) => a.id - b.id)
    const initialSubmitData = allTestcases.map(() => ({
      status: { id: 1, description: 'Queued' },
    }))
    setSubmitData(initialSubmitData)
    setActiveCase(0)

    if (isTestPanelCollapsed) {
      testPanelRef.current?.expand()
    }

    try {
      const submitUrl = contestId
        ? `engine/submit-stream/?mode=submit&contest_id=${contestId}`
        : 'engine/submit-stream/?mode=submit'
      const response = await apiFetch(submitUrl, {
        method: 'POST',
        body: JSON.stringify({
          problem_id: problem.id,
          source_code: code,
          language: language,
          language_id: LanguageCodes[language],
          contest_id: contestId,
        }),
      })

      if (response.status === 401) {
        throw new Error('Authentication failed. Please login again.')
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Stream reader not available')

      const decoder = new TextDecoder()
      let currentResults = [...initialSubmitData]
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const payload = JSON.parse(line)
            if (payload.status === 'case_result') {
              const res = payload.data
              currentResults[res.index] = res
              setSubmitData([...currentResults])
            } else if (payload.status === 'complete') {
              const finalSub: Solution = {
                id: payload.solution_id || 0,
                user: user!,
                problem: problem.id,
                code: code ?? '',
                language: language,
                language_display: payload.language_display || language,
                status: payload.total_status,
                status_display: payload.total_status,
                testcase_results: currentResults,
                created_at: new Date().toISOString(),
              }
              setFinalSubmission(finalSub)

              if (payload.total_status === 'Accepted') {
                toast.success('All test cases passed!')
              } else if (payload.compile_output) {
                setError(payload.compile_output)
                toast.error('Compilation Error')
              } else {
                toast.error(`Solution failed: ${payload.total_status}`)
              }
              setIsLoading(false)
              mutate(`solutions/?problem_id=${problem.id}`)
            } else if (payload.status === 'error') {
              setError(payload.message)
              setIsLoading(false)
            }
          } catch (e) {
            console.error('JSON parse error on line:', line, e)
          }
        }
      }
    } catch (err: any) {
      console.error('Error streaming submission:', err)
      setError(err.message || 'Failed to process submission stream')
      setIsLoading(false)
    }
  }

  return (
    <ResizablePanel
      ref={ref}
      defaultSize={50}
      minSize={0}
      collapsible={true}
      className="h-full flex flex-col"
    >
      <div className="h-full flex flex-col bg-[#1e1e1e] relative overflow-hidden">
        <AnimatePresence>
          {finalSubmission && (
            <SubmissionResult
              solution={finalSubmission}
              onClose={() => setFinalSubmission(null)}
              testcases={problem.testcases}
              history={history}
              variables={problem.variables}
            />
          )}
        </AnimatePresence>

        <ResizablePanelGroup
          autoSaveId="coderacer-vertical-layout"
          direction="vertical"
          className="flex-1"
        >
          <ResizablePanel
            defaultSize={60}
            minSize={15}
            className="flex flex-col"
          >
            <div className="h-full flex flex-col">
              <EditorToolbar
                onReset={handleReset}
                language={language}
                setLanguage={setLanguage}
                availableLanguages={availableLanguages}
                maximizedSide={maximizedSide}
                onMaximize={handleMaximize}
                onRestore={onRestore}
              />
              <div className="flex-1 min-h-0">
                {code !== null && (
                  <Editor
                    height="100%"
                    language={language.toLowerCase()}
                    value={code}
                    theme="vs-dark"
                    onChange={(value) => setCode(value ?? '')}
                    onMount={handleEditorDidMount}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: 'on',
                      roundedSelection: false,
                      scrollBeyondLastLine: false,
                      readOnly: false,
                      automaticLayout: true,
                    }}
                  />
                )}
              </div>
            </div>
          </ResizablePanel>
          <ResizableHandle
            withHandle
            className={
              isTestPanelCollapsed ? 'opacity-0 pointer-events-none' : ''
            }
          />
          <ResizablePanel
            defaultSize={40}
            minSize={0}
            collapsible={true}
            ref={testPanelRef}
            onCollapse={() => setIsTestPanelCollapsed(true)}
            onExpand={() => setIsTestPanelCollapsed(false)}
            className="flex flex-col"
          >
            <div className="h-full">
              <TestPanel
                problem={problem}
                user={user}
                language={language}
                runData={runData}
                submitData={submitData}
                isLoading={isLoading}
                error={error}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                activeCase={activeCase}
                setActiveCase={setActiveCase}
                sampleTestcases={sampleTestcases}
                setSampleTestcases={setSampleTestcases}
                isContestMode={isContestMode}
              />
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>

        <div className="p-2 flex justify-between items-center bg-surface-dark border-t border-surface-border shrink-0">
          <button
            onClick={toggleTestPanel}
            className={`text-xs px-3 py-1.5 rounded flex items-center gap-2 transition-colors ${
              isTestPanelCollapsed
                ? 'text-white bg-surface-border hover:bg-muted'
                : 'text-gray-400 hover:text-white hover:bg-surface-border'
            }`}
          >
            <span className="material-symbols-outlined text-lg">
              {isTestPanelCollapsed
                ? 'keyboard_arrow_up'
                : 'keyboard_arrow_down'}
            </span>
            Console
          </button>
          <div className="flex gap-2">
            {user ? (
              <>
                <button
                  className="bg-primary hover:bg-primary/90 text-white px-4 py-1.5 rounded text-sm font-bold transition-all active:scale-95 disabled:opacity-50"
                  onClick={() => runCode()}
                  disabled={isLoading}
                >
                  Run
                </button>
                <button
                  className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-1.5 rounded text-sm font-bold transition-all active:scale-95 disabled:opacity-50"
                  disabled={isLoading}
                  onClick={() => submitCode()}
                >
                  Submit
                </button>
              </>
            ) : (
              <div className="flex gap-2">
                <Link href="/login">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-white hover:bg-surface-border text-xs h-8"
                  >
                    Sign In to Run
                  </Button>
                </Link>
                <Link href="/signup">
                  <Button
                    size="sm"
                    className="bg-primary hover:bg-primary/90 text-white text-xs h-8"
                  >
                    Sign Up
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </ResizablePanel>
  )
}

export default CodeEditor
