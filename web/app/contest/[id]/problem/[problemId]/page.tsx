'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import ProblemDescription from '@/components/problem/problem-description'
import CodeEditor from '@/components/problem/code-editor'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import useSWR from 'swr'
import { ImperativePanelHandle } from 'react-resizable-panels'
import { DescriptionSkeleton, EditorSkeleton } from '@/components/loader'
import PageTransition from '@/components/page-transition'
import { useAuth } from '@/components/auth-provider'
import { apiFetcher, formatInUserTimezone } from '@/lib/utils'
import {
  ContestProblemDetail,
  ContestLeaderboardResponse,
  Problem,
  Difficulty,
} from '@/lib/models'
import Link from 'next/link'
import Logo from '@/components/logo'
import { UserMenu } from '@/components/header'
import DifficultyBadge from '@/components/difficulty-badge'
import {
  Timer,
  ChevronLeft,
  ChevronRight,
  ListOrdered,
  Award,
  CheckCircle2,
  XCircle,
  X,
  AlertCircle,
  Trophy,
  RefreshCw,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { toast } from 'sonner'

export default function ContestProblemPage() {
  const params = useParams()
  const contestId = params.id as string
  const problemId = params.problemId as string
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  const [maximizedSide, setMaximizedSide] = useState<'left' | 'right' | null>(
    null
  )
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [sidebarTab, setSidebarTab] = useState<'problems' | 'leaderboard'>(
    'problems'
  )

  const leftPanelRef = useRef<ImperativePanelHandle>(null)
  const rightPanelRef = useRef<ImperativePanelHandle>(null)

  // Fetch contest problem details
  const {
    data: contestProblem,
    error: problemError,
    isLoading: problemLoading,
    mutate: mutateContestProblem,
  } = useSWR<ContestProblemDetail>(
    `contests/${contestId}/problems/${problemId}/`,
    apiFetcher,
    { refreshInterval: 15000 }
  )

  // Fetch live contest leaderboard
  const {
    data: leaderboardData,
    isLoading: leaderboardLoading,
    mutate: refreshLeaderboard,
  } = useSWR<ContestLeaderboardResponse>(
    `contests/${contestId}/leaderboard/`,
    apiFetcher,
    { refreshInterval: 10000 }
  )

  const isLoading = problemLoading || authLoading

  const handleMaximizeLeft = () => {
    if (leftPanelRef.current && rightPanelRef.current) {
      rightPanelRef.current.collapse()
      leftPanelRef.current.resize(100)
      setMaximizedSide('left')
    }
  }

  const handleMaximizeRight = () => {
    if (leftPanelRef.current && rightPanelRef.current) {
      leftPanelRef.current.collapse()
      rightPanelRef.current.resize(100)
      setMaximizedSide('right')
    }
  }

  const handleRestore = () => {
    if (leftPanelRef.current && rightPanelRef.current) {
      leftPanelRef.current.expand()
      rightPanelRef.current.expand()
      leftPanelRef.current.resize(50)
      rightPanelRef.current.resize(50)
      setMaximizedSide(null)
    }
  }

  if (problemError && !isLoading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-background-dark text-white p-4">
        <AlertCircle className="size-12 text-red-500 mb-3" />
        <h2 className="text-xl font-bold">Error Loading Problem</h2>
        <p className="text-gray-400 text-xs mt-1 mb-4">
          {problemError.message || 'Contest problem could not be loaded.'}
        </p>
        <Link href={`/contest/${contestId}`}>
          <button className="bg-primary hover:bg-primary/90 text-white font-bold px-4 py-2 rounded-lg text-xs">
            Back to Contest Lobby
          </button>
        </Link>
      </div>
    )
  }

  // Construct mock Problem object for standard components
  const mockProblem: Problem | null = contestProblem
    ? {
        id: contestProblem.problem_id,
        name: contestProblem.name,
        problem_description: contestProblem.problem_description,
        difficulty: contestProblem.difficulty,
        codeblocks: contestProblem.codeblocks,
        testcases: contestProblem.testcases,
        variables: contestProblem.variables,
        tags: [],
        total_solutions: 0,
        total_testcases: contestProblem.testcases?.length || 0,
        is_multi: false,
      }
    : null

  return (
    <PageTransition>
      <div className="h-screen flex flex-col overflow-hidden bg-background-dark text-white">
        {/* Contest Header Bar */}
        <header className="h-12.5 border-b border-surface-border bg-surface-dark px-4 flex items-center justify-between shrink-0 z-40">
          {/* Left: Logo & Contest Info & Navigation */}
          <div className="flex items-center gap-3 md:gap-5">
            <Logo variant="problem" />

            <div className="h-4 w-px bg-gray-700 hidden sm:block" />

            <Link
              href={`/contest/${contestId}`}
              className="text-xs font-bold text-gray-300 hover:text-white flex items-center gap-1.5 transition-colors"
            >
              <Trophy className="size-4 text-yellow-500" />
              <span className="hidden md:inline">
                {contestProblem?.contest_title || 'Contest'}
              </span>
              <span className="text-[11px] bg-primary/20 text-primary px-2 py-0.5 rounded font-bold">
                Q{contestProblem?.order || 1} ({contestProblem?.points || 3}{' '}
                pts)
              </span>
            </Link>

            {/* Problem List & Leaderboard Drawer Button */}
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="bg-surface-border hover:bg-muted text-gray-300 hover:text-white px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors border border-surface-border"
            >
              <ListOrdered className="size-3.5 text-primary" />
              <span>Problems & Leaderboard</span>
            </button>

            {/* Prev / Next navigation */}
            <div className="flex items-center gap-1">
              <button
                disabled={!contestProblem?.prev_problem_id}
                onClick={() =>
                  contestProblem?.prev_problem_id &&
                  router.push(
                    `/contest/${contestId}/problem/${contestProblem.prev_problem_id}`
                  )
                }
                title="Previous Question"
                className="size-7 rounded bg-surface-border hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center text-gray-300 transition-colors"
              >
                <ChevronLeft className="size-4" />
              </button>
              <button
                disabled={!contestProblem?.next_problem_id}
                onClick={() =>
                  contestProblem?.next_problem_id &&
                  router.push(
                    `/contest/${contestId}/problem/${contestProblem.next_problem_id}`
                  )
                }
                title="Next Question"
                className="size-7 rounded bg-surface-border hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center text-gray-300 transition-colors"
              >
                <ChevronRight className="size-4" />
              </button>
            </div>
          </div>

          {/* Center: Live Timer on Top */}
          <div className="flex items-center justify-center">
            {contestProblem && (
              <ContestHeaderTimer
                endTime={contestProblem.contest_end_time}
                status={contestProblem.contest_status}
              />
            )}
          </div>

          {/* Right: User Menu */}
          <div className="flex items-center gap-3">
            <UserMenu />
          </div>
        </header>

        {/* Workspace Panels */}
        <ResizablePanelGroup
          autoSaveId="coderacer-contest-layout"
          direction="horizontal"
        >
          {isLoading || !mockProblem ? (
            <ResizablePanel defaultSize={50} minSize={20}>
              <DescriptionSkeleton />
            </ResizablePanel>
          ) : (
            <ProblemDescription
              ref={leftPanelRef}
              problem={mockProblem}
              maximizedSide={maximizedSide}
              onMaximize={handleMaximizeLeft}
              onRestore={handleRestore}
              isContestMode={true}
              contestInfo={{
                contest_id: Number(contestId),
                order: contestProblem?.order,
                points: contestProblem?.points,
                attempted_count: contestProblem?.attempted_count,
                submitted_count: contestProblem?.submitted_count,
                accepted_count: contestProblem?.accepted_count,
              }}
            />
          )}

          <ResizableHandle withHandle />

          {isLoading || !mockProblem ? (
            <ResizablePanel defaultSize={50} minSize={20}>
              <EditorSkeleton />
            </ResizablePanel>
          ) : (
            <CodeEditor
              ref={rightPanelRef}
              user={user}
              problem={mockProblem}
              maximizedSide={maximizedSide}
              onMaximize={handleMaximizeRight}
              onRestore={handleRestore}
              isContestMode={true}
              contestId={Number(contestId)}
            />
          )}
        </ResizablePanelGroup>

        {/* Sidebar Drawer Modal with 2 Tabs: Problems List & Live Leaderboard */}
        {isSidebarOpen && (
          <div className="fixed inset-0 z-50 flex">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
              onClick={() => setIsSidebarOpen(false)}
            />

            {/* Drawer */}
            <div className="relative z-10 w-full max-w-md bg-surface-dark border-r border-surface-border h-full shadow-2xl flex flex-col animate-in slide-in-from-left duration-200">
              {/* Drawer Header */}
              <div className="p-4 border-b border-surface-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Trophy className="size-5 text-yellow-500" />
                  <h3 className="font-bold text-sm text-white">
                    {contestProblem?.contest_title || 'Contest'}
                  </h3>
                </div>
                <button
                  onClick={() => setIsSidebarOpen(false)}
                  className="size-7 rounded hover:bg-surface-border flex items-center justify-center text-gray-400 hover:text-white"
                >
                  <X className="size-4" />
                </button>
              </div>

              {/* Drawer Tabs */}
              <div className="flex border-b border-surface-border bg-background-dark/50">
                <button
                  onClick={() => setSidebarTab('problems')}
                  className={`flex-1 py-2.5 text-xs font-bold text-center border-b-2 transition-all flex items-center justify-center gap-1.5 ${
                    sidebarTab === 'problems'
                      ? 'text-primary border-primary bg-primary/5'
                      : 'text-gray-400 hover:text-white border-transparent'
                  }`}
                >
                  <ListOrdered className="size-3.5" />
                  Problems ({contestProblem?.contest_problems?.length || 0})
                </button>
                <button
                  onClick={() => setSidebarTab('leaderboard')}
                  className={`flex-1 py-2.5 text-xs font-bold text-center border-b-2 transition-all flex items-center justify-center gap-1.5 ${
                    sidebarTab === 'leaderboard'
                      ? 'text-primary border-primary bg-primary/5'
                      : 'text-gray-400 hover:text-white border-transparent'
                  }`}
                >
                  <Award className="size-3.5" />
                  Live Leaderboard
                </button>
              </div>

              {/* Drawer Tab Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {sidebarTab === 'problems' && (
                  <div className="space-y-2">
                    {contestProblem?.contest_problems?.map((p) => {
                      const isCurrent = p.problem_id === Number(problemId)
                      const isDone = p.user_status === 'done'
                      const isAttempted = p.user_status === 'attempted'

                      return (
                        <div
                          key={p.id}
                          onClick={() => {
                            router.push(
                              `/contest/${contestId}/problem/${p.problem_id}`
                            )
                            setIsSidebarOpen(false)
                          }}
                          className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                            isCurrent
                              ? 'bg-primary/10 border-primary/50 text-white'
                              : 'bg-background-dark/70 border-surface-border hover:border-gray-600 text-gray-300'
                          }`}
                        >
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            {isDone ? (
                              <CheckCircle2 className="size-4.5 text-green-500 shrink-0" />
                            ) : isAttempted ? (
                              <div className="size-4.5 rounded-full border-2 border-yellow-500 flex items-center justify-center text-[9px] font-bold text-yellow-500 shrink-0">
                                -
                              </div>
                            ) : (
                              <div className="size-4.5 rounded-full border border-gray-600 shrink-0" />
                            )}
                            <div className="truncate">
                              <span className="font-bold text-xs block truncate">
                                Q{p.order}. {p.name}
                              </span>
                              <span className="text-[10px] text-gray-500 font-semibold">
                                {p.difficulty} · {p.points} Points
                              </span>
                            </div>
                          </div>

                          <div className="text-right shrink-0">
                            <span className="text-xs font-bold text-primary">
                              {p.points} pts
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}

                {sidebarTab === 'leaderboard' && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-[11px] text-gray-400 pb-1">
                      <span>Live Rankings</span>
                      <button
                        onClick={() => refreshLeaderboard()}
                        className="text-primary hover:underline flex items-center gap-1"
                      >
                        <RefreshCw className="size-3" /> Refresh
                      </button>
                    </div>

                    {leaderboardLoading ? (
                      <div className="space-y-2">
                        {[1, 2, 3, 4, 5].map((n) => (
                          <div
                            key={n}
                            className="h-10 bg-background-dark/50 rounded-lg animate-pulse"
                          />
                        ))}
                      </div>
                    ) : leaderboardData?.leaderboard &&
                      leaderboardData.leaderboard.length > 0 ? (
                      <div className="space-y-1.5">
                        {leaderboardData.leaderboard.map((entry, idx) => {
                          const isCurrentUser =
                            user && entry.user_id === user.id
                          return (
                            <div
                              key={entry.user_id}
                              className={`flex items-center justify-between p-2.5 rounded-lg border transition-colors ${
                                isCurrentUser
                                  ? 'bg-primary/10 border-primary/40 font-bold'
                                  : 'bg-background-dark/60 border-surface-border'
                              }`}
                            >
                              <div className="flex items-center gap-2.5 min-w-0">
                                <span
                                  className={`w-5 text-center text-xs font-bold ${
                                    entry.rank === 1
                                      ? 'text-yellow-400 font-black'
                                      : entry.rank === 2
                                        ? 'text-slate-300 font-bold'
                                        : entry.rank === 3
                                          ? 'text-amber-500 font-bold'
                                          : 'text-gray-500'
                                  }`}
                                >
                                  #{entry.rank || idx + 1}
                                </span>
                                <Avatar className="size-6 border border-surface-border shrink-0">
                                  <AvatarImage src={entry.profile_picture} />
                                  <AvatarFallback>
                                    {entry.username
                                      .substring(0, 2)
                                      .toUpperCase()}
                                  </AvatarFallback>
                                </Avatar>
                                <span className="text-xs text-gray-200 truncate">
                                  {entry.name || entry.username}
                                  {isCurrentUser && (
                                    <span className="text-[10px] text-primary ml-1">
                                      (You)
                                    </span>
                                  )}
                                </span>
                              </div>

                              <div className="text-right shrink-0">
                                <span className="text-xs font-bold text-primary">
                                  {entry.score} pts
                                </span>
                                <div className="text-[10px] text-gray-500 font-mono">
                                  {Math.floor(entry.penalty_seconds / 60)}m
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="py-8 text-center text-xs text-gray-500">
                        No submissions on leaderboard yet.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  )
}

function ContestHeaderTimer({
  endTime,
  status,
}: {
  endTime: string
  status: string
}) {
  const [secondsRemaining, setSecondsRemaining] = useState<number>(0)

  useEffect(() => {
    const calculateTime = () => {
      const now = new Date().getTime()
      const end = new Date(endTime).getTime()
      const diff = Math.max(0, Math.floor((end - now) / 1000))
      setSecondsRemaining(diff)
    }

    calculateTime()
    const timer = setInterval(calculateTime, 1000)
    return () => clearInterval(timer)
  }, [endTime])

  const hours = Math.floor(secondsRemaining / 3600)
  const minutes = Math.floor((secondsRemaining % 3600) / 60)
  const seconds = secondsRemaining % 60

  const isLowTime = secondsRemaining < 300 && secondsRemaining > 0 // < 5 mins
  const isEnded = secondsRemaining === 0

  return (
    <div
      className={`flex items-center gap-1.5 font-mono text-xs font-bold px-3 py-1 rounded-full border transition-all ${
        isEnded
          ? 'bg-red-950/40 text-red-400 border-red-800/50'
          : isLowTime
            ? 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse'
            : 'bg-black/30 text-gray-200 border-surface-border'
      }`}
    >
      <Timer
        className={`size-3.5 ${isLowTime ? 'text-red-400' : 'text-primary'}`}
      />
      <span>
        {isEnded
          ? 'Contest Ended'
          : `${String(hours).padStart(2, '0')}:${String(minutes).padStart(
              2,
              '0'
            )}:${String(seconds).padStart(2, '0')}`}
      </span>
    </div>
  )
}
