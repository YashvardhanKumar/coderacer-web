'use client'

import { useState, useMemo } from 'react'
import {
  Solution,
  Status,
  TestcaseList,
  LanguageDisplayNames,
  Variable,
} from '@/lib/models'
import {
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  X,
  Clock,
  Zap,
  Database,
} from 'lucide-react'
import { formatInUserTimezone } from '@/lib/utils'
import TestResultDetail from './test-result-detail'
import CodeBlock from '@/components/code-block'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { motion, AnimatePresence } from 'framer-motion'

interface SubmissionResultProps {
  solution: Solution | null
  onClose: () => void
  history?: Solution[]
  testcases: TestcaseList[]
  variables?: Variable[]
}

export default function SubmissionResult({
  solution,
  onClose,
  history = [],
  testcases,
  variables,
}: SubmissionResultProps) {
  const [copied, setCopied] = useState(false)

  const stats = useMemo(() => {
    if (!solution || !solution.testcase_results) return null

    const results = solution.testcase_results as any[]
    const maxMemory = results.reduce(
      (acc, curr) => Math.max(acc, parseFloat(curr.memory) || 0),
      0
    )
    const peakUserTime = results.reduce(
      (acc, curr) => Math.max(acc, parseFloat(curr.user_time_ms) || 0),
      0
    )
    return {
      time: Math.round(peakUserTime),
      memory: (maxMemory / 1024).toFixed(2),
    }
  }, [solution])

  const chartData = useMemo(() => {
    if (!history || history.length === 0) return []

    return [...history].reverse().map((s, index) => {
      const results = (s.testcase_results as any[]) || []
      const userTime = results.reduce(
        (acc, curr) => acc + (parseFloat(curr.user_time_ms) || 0),
        0
      )
      const time = Math.round(userTime)
      const memory =
        results.reduce(
          (acc, curr) => Math.max(acc, parseFloat(curr.memory) || 0),
          0
        ) / 1024

      return {
        name: index + 1,
        time,
        memory: parseFloat(memory.toFixed(2)),
        status: s.status,
        id: s.id,
      }
    })
  }, [history])

  const firstFailedResult = useMemo(() => {
    if (
      !solution ||
      solution.status === Status.SUCCESS ||
      !solution.testcase_results
    )
      return null

    const results = solution.testcase_results as any[]
    const failedIndex = results.findIndex((r) => r.status?.id !== 3)

    if (failedIndex === -1) return null

    return {
      result: results[failedIndex],
      testcase: testcases[failedIndex],
      index: failedIndex,
    }
  }, [solution, testcases])

  const copyCode = () => {
    if (!solution?.code) return
    navigator.clipboard.writeText(solution.code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!solution) return null

  const isAccepted = solution.status === Status.SUCCESS

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="absolute inset-0 bg-background-dark z-50 flex flex-col overflow-hidden"
    >
      {/* Header */}
      <div className="h-12 border-b border-surface-border flex items-center justify-between px-4 bg-surface-dark shrink-0">
        <div className="flex items-center gap-3">
          {isAccepted ? (
            <div className="flex items-center gap-2 text-green-500 font-bold">
              <CheckCircle2 size={20} />
              <span>Accepted</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-500 font-bold">
              <XCircle size={20} />
              <span>{solution.status_display}</span>
            </div>
          )}
          <span className="text-gray-500 text-xs">
            Submitted{' '}
            {formatInUserTimezone(solution.created_at, 'MMM d, yyyy HH:mm')}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors p-1"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-20">
        {isAccepted ? (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surface-dark p-4 rounded-xl border border-surface-border flex items-center gap-4">
                <div className="bg-green-500/10 p-3 rounded-lg text-green-500">
                  <Clock size={24} />
                </div>
                <div>
                  <p className="text-gray-400 text-xs font-medium uppercase tracking-wider">
                    Runtime
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.time}{' '}
                    <span className="text-sm font-normal text-gray-500">
                      ms
                    </span>
                  </p>
                </div>
              </div>
              <div className="bg-surface-dark p-4 rounded-xl border border-surface-border flex items-center gap-4">
                <div className="bg-blue-500/10 p-3 rounded-lg text-blue-500">
                  <Database size={24} />
                </div>
                <div>
                  <p className="text-gray-400 text-xs font-medium uppercase tracking-wider">
                    Memory
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.memory}{' '}
                    <span className="text-sm font-normal text-gray-500">
                      MB
                    </span>
                  </p>
                </div>
              </div>
            </div>

            {/* Graphs */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-surface-dark p-4 rounded-xl border border-surface-border space-y-4">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Zap size={16} className="text-yellow-500" />
                  Runtime Distribution
                </h4>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient
                          id="colorTime"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="5%"
                            stopColor="#22c55e"
                            stopOpacity={0.3}
                          />
                          <stop
                            offset="95%"
                            stopColor="#22c55e"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#333"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="name"
                        stroke="#666"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        stroke="#666"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e1e1e',
                          border: '1px solid #333',
                          borderRadius: '8px',
                        }}
                        itemStyle={{ color: '#22c55e' }}
                      />
                      <Area
                        type="monotone"
                        dataKey="time"
                        stroke="#22c55e"
                        fillOpacity={1}
                        fill="url(#colorTime)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-surface-dark p-4 rounded-xl border border-surface-border space-y-4">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Database size={16} className="text-blue-500" />
                  Memory Distribution
                </h4>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient
                          id="colorMem"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="5%"
                            stopColor="#3b82f6"
                            stopOpacity={0.3}
                          />
                          <stop
                            offset="95%"
                            stopColor="#3b82f6"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#333"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="name"
                        stroke="#666"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        stroke="#666"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e1e1e',
                          border: '1px solid #333',
                          borderRadius: '8px',
                        }}
                        itemStyle={{ color: '#3b82f6' }}
                      />
                      <Area
                        type="monotone"
                        dataKey="memory"
                        stroke="#3b82f6"
                        fillOpacity={1}
                        fill="url(#colorMem)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* Failure State */
          <div className="space-y-6">
            <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
              <h4 className="text-sm font-bold text-red-500 mb-4 flex items-center gap-2">
                <AlertCircle size={18} />
                Failed Test Case{' '}
                {firstFailedResult ? firstFailedResult.index + 1 : ''}
              </h4>
              {firstFailedResult && (
                <TestResultDetail
                  result={firstFailedResult.result}
                  testcase={firstFailedResult.testcase}
                  variables={variables}
                />
              )}
            </div>
          </div>
        )}

        {/* Code Section */}
        <div className="space-y-4 prose prose-invert max-w-none prose-sm">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">code</span>
              Submitted Code
            </h4>
          </div>
          <CodeBlock
            code={solution.code}
            language={solution.language_display || solution.language}
          />
        </div>
      </div>
    </motion.div>
  )
}

function AlertCircle(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  )
}
