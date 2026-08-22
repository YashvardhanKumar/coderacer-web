'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Header from '@/components/header'
import PageTransition from '@/components/page-transition'
import {
  Contest,
  ContestLeaderboardResponse,
  ContestProblemSummary,
  Difficulty,
} from '@/lib/models'
import { apiFetch, apiFetcher, formatInUserTimezone } from '@/lib/utils'
import useSWR, { mutate } from 'swr'
import Link from 'next/link'
import { useAuth } from '@/components/auth-provider'
import { toast } from 'sonner'
import DifficultyBadge from '@/components/difficulty-badge'
import {
  Trophy,
  Calendar,
  Clock,
  Users,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Lock,
  Flame,
  Award,
  ChevronLeft,
  ArrowRight,
  Sparkles,
  RefreshCw,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

export default function ContestDetailPage() {
  const { id } = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'problems' | 'leaderboard'>(
    'problems'
  )
  const [isRegistering, setIsRegistering] = useState(false)

  const {
    data: contest,
    error,
    isLoading,
  } = useSWR<Contest>(`contests/${id}/`, apiFetcher, {
    refreshInterval: 15000,
  })

  const {
    data: leaderboardData,
    isLoading: isLeaderboardLoading,
    mutate: refreshLeaderboard,
  } = useSWR<ContestLeaderboardResponse>(
    `contests/${id}/leaderboard/`,
    apiFetcher,
    {
      refreshInterval: contest?.status === 'ONGOING' ? 8000 : 30000,
    }
  )

  const handleRegister = async () => {
    if (!user) {
      toast.error('Please sign in to register for the contest')
      router.push('/login')
      return
    }

    setIsRegistering(true)
    try {
      const res = await apiFetch(`contests/${id}/register/`, { method: 'POST' })
      if (res.ok) {
        toast.success('Successfully registered for the contest!')
        mutate(`contests/${id}/`)
        refreshLeaderboard()
      } else {
        const data = await res.json()
        toast.error(data.error || 'Failed to register')
      }
    } catch (err: any) {
      toast.error(err.message || 'Error registering')
    } finally {
      setIsRegistering(false)
    }
  }

  const handleUnregister = async () => {
    setIsRegistering(true)
    try {
      const res = await apiFetch(`contests/${id}/unregister/`, {
        method: 'POST',
      })
      if (res.ok) {
        toast.info('Unregistered from the contest')
        mutate(`contests/${id}/`)
        refreshLeaderboard()
      } else {
        const data = await res.json()
        toast.error(data.error || 'Failed to unregister')
      }
    } catch (err: any) {
      toast.error(err.message || 'Error unregistering')
    } finally {
      setIsRegistering(false)
    }
  }

  if (error && !isLoading) {
    return (
      <div className="min-h-screen bg-background-dark text-white flex flex-col">
        <Header />
        <div className="flex-1 flex flex-col items-center justify-center p-4">
          <AlertCircle className="size-12 text-red-500 mb-3" />
          <h2 className="text-xl font-bold">Contest Not Found</h2>
          <p className="text-gray-400 text-sm mt-1 mb-4">
            The requested contest does not exist or has not been published.
          </p>
          <Link href="/contest">
            <button className="bg-primary hover:bg-primary/90 text-white font-bold px-4 py-2 rounded-lg text-sm">
              Back to Contests
            </button>
          </Link>
        </div>
      </div>
    )
  }

  if (isLoading || !contest) {
    return (
      <div className="min-h-screen bg-background-dark text-white flex flex-col">
        <Header />
        <div className="max-w-6xl w-full mx-auto p-8 space-y-6 animate-pulse">
          <div className="h-40 bg-surface-dark rounded-2xl" />
          <div className="h-64 bg-surface-dark rounded-2xl" />
        </div>
      </div>
    )
  }

  const isLive = contest.status === 'ONGOING'
  const isUpcoming = contest.status === 'UPCOMING'
  const isPast = contest.status === 'PAST'

  return (
    <PageTransition>
      <div className="min-h-screen bg-background-dark text-white flex flex-col">
        <Header />

        <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
          {/* Back Navigation */}
          <Link
            href="/contest"
            className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
          >
            <ChevronLeft className="size-4" /> Back to all contests
          </Link>

          {/* Contest Hero Header Card */}
          <div className="relative overflow-hidden bg-surface-dark border border-surface-border rounded-2xl p-6 sm:p-8 shadow-xl">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div className="space-y-3 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-bold px-2.5 py-0.5 rounded-full uppercase ${
                      contest.is_weekly
                        ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                        : 'bg-slate-700 text-gray-300'
                    }`}
                  >
                    {contest.is_weekly ? 'WEEKLY RUN' : 'CUSTOM CONTEST'}
                  </span>
                  {isLive && (
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse flex items-center gap-1">
                      <span className="size-2 rounded-full bg-emerald-500 inline-block" />
                      Live Now
                    </span>
                  )}
                  {isPast && (
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-gray-800 text-gray-400">
                      Ended
                    </span>
                  )}
                </div>

                <h1 className="text-2xl sm:text-3xl font-black text-white">
                  {contest.title}
                </h1>

                <p className="text-xs sm:text-sm text-gray-300">
                  {contest.description ||
                    'Solve all problems to maximize points. Ranking order is determined by total score and finish time.'}
                </p>

                <div className="flex items-center gap-5 text-xs text-gray-400 pt-1 flex-wrap">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="size-4 text-primary" />
                    {formatInUserTimezone(
                      contest.start_time,
                      'EEE, MMM d, yyyy · HH:mm'
                    )}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock className="size-4 text-primary" />
                    {contest.duration_minutes} Minutes
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Users className="size-4 text-primary" />
                    {contest.registered_count} Registered
                  </span>
                  {contest.user_rank && (
                    <span className="flex items-center gap-1.5 text-yellow-400 font-bold">
                      <Award className="size-4" />
                      Your Rank: #{contest.user_rank} ({contest.user_score} pts)
                    </span>
                  )}
                </div>
              </div>

              {/* Countdown & Action Button */}
              <div className="flex flex-col items-center sm:items-end gap-4 w-full md:w-auto bg-background-dark/80 p-5 rounded-xl border border-surface-border">
                <ContestCountdown contest={contest} />

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  {isLive ? (
                    contest.problems && contest.problems.length > 0 ? (
                      <Link
                        href={`/contest/${contest.id}/problem/${contest.problems[0].problem_id}`}
                        className="w-full sm:w-auto"
                      >
                        <button className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-2.5 rounded-lg text-sm transition-all shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2">
                          <Flame className="size-4 animate-bounce" />
                          Solve Q1 Now
                        </button>
                      </Link>
                    ) : (
                      <span className="text-xs text-gray-400">
                        Loading problems...
                      </span>
                    )
                  ) : isUpcoming ? (
                    contest.is_registered ? (
                      <div className="flex items-center gap-2">
                        <span className="text-emerald-400 font-bold text-xs flex items-center gap-1 bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 rounded-lg">
                          <CheckCircle2 className="size-4" /> Registered
                        </span>
                        <button
                          onClick={handleUnregister}
                          disabled={isRegistering}
                          className="text-xs text-red-400 hover:text-red-300 underline transition-colors px-2"
                        >
                          Unregister
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={handleRegister}
                        disabled={isRegistering}
                        className="w-full sm:w-auto bg-primary hover:bg-primary/90 text-white font-bold px-6 py-2.5 rounded-lg text-sm transition-all shadow-lg shadow-primary/20"
                      >
                        {isRegistering
                          ? 'Registering...'
                          : 'Register for Contest'}
                      </button>
                    )
                  ) : (
                    <span className="text-xs text-gray-400 font-medium">
                      Contest Concluded
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs (Problems & Leaderboard) */}
          <div className="flex items-center gap-3 border-b border-surface-border">
            <button
              onClick={() => setActiveTab('problems')}
              className={`flex items-center gap-2 pb-3 px-2 text-sm font-bold border-b-2 transition-all ${
                activeTab === 'problems'
                  ? 'text-primary border-primary'
                  : 'text-gray-400 hover:text-white border-transparent'
              }`}
            >
              <Trophy className="size-4" />
              Problems List (
              {contest.problems?.length || contest.total_problems || 0})
            </button>
            <button
              onClick={() => setActiveTab('leaderboard')}
              className={`flex items-center gap-2 pb-3 px-2 text-sm font-bold border-b-2 transition-all ${
                activeTab === 'leaderboard'
                  ? 'text-primary border-primary'
                  : 'text-gray-400 hover:text-white border-transparent'
              }`}
            >
              <Award className="size-4" />
              Leaderboard ({leaderboardData?.total_participants || 0})
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'problems' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              {isUpcoming ? (
                <div className="bg-surface-dark border border-surface-border rounded-xl p-8 text-center space-y-4">
                  <Lock className="size-12 text-primary mx-auto opacity-70" />
                  <div className="space-y-1">
                    <h3 className="text-lg font-bold text-white">
                      Problems Are Locked Until Contest Starts
                    </h3>
                    <p className="text-xs text-gray-400 max-w-md mx-auto">
                      All problems are fresh and new. They will automatically
                      unlock as soon as the countdown hits zero on{' '}
                      {formatInUserTimezone(
                        contest.start_time,
                        'MMM d, yyyy · HH:mm'
                      )}
                      .
                    </p>
                  </div>
                  {contest.problems && (
                    <div className="max-w-md mx-auto grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
                      {contest.problems.map((p) => (
                        <div
                          key={p.order}
                          className="bg-background-dark/80 border border-surface-border p-3 rounded-lg text-center"
                        >
                          <span className="text-xs font-bold text-primary block">
                            Q{p.order}
                          </span>
                          <span className="text-[11px] text-gray-400 font-semibold">
                            {p.points} Points
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : contest.problems && contest.problems.length > 0 ? (
                <div className="bg-surface-dark border border-surface-border rounded-xl overflow-hidden shadow-lg">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-background-dark/60 text-gray-400 text-xs uppercase tracking-wider border-b border-surface-border">
                      <tr>
                        <th className="px-6 py-3.5 font-medium">Status</th>
                        <th className="px-6 py-3.5 font-medium">Title</th>
                        <th className="px-6 py-3.5 font-medium">Score</th>
                        <th className="px-6 py-3.5 font-medium">Difficulty</th>
                        <th className="px-6 py-3.5 font-medium">
                          Participation
                        </th>
                        <th className="px-6 py-3.5 font-medium text-right">
                          Action
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-border text-sm">
                      {contest.problems.map((prob) => {
                        const isDone = prob.user_status === 'done'
                        const isAttempted = prob.user_status === 'attempted'
                        return (
                          <tr
                            key={prob.id}
                            className="hover:bg-white/5 transition-colors group cursor-pointer"
                            onClick={() =>
                              router.push(
                                `/contest/${contest.id}/problem/${prob.problem_id}`
                              )
                            }
                          >
                            <td className="px-6 py-4">
                              {isDone ? (
                                <CheckCircle2 className="size-5 text-green-500" />
                              ) : isAttempted ? (
                                <div
                                  className="size-5 rounded-full border-2 border-yellow-500 flex items-center justify-center text-[10px] font-bold text-yellow-500"
                                  title="Attempted"
                                >
                                  -
                                </div>
                              ) : (
                                <div className="size-5 rounded-full border border-gray-600" />
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <span className="font-bold text-white group-hover:text-primary transition-colors">
                                Q{prob.order}. {prob.name}
                              </span>
                            </td>
                            <td className="px-6 py-4 font-bold text-primary text-xs">
                              {prob.points} pts
                            </td>
                            <td className="px-6 py-4">
                              <DifficultyBadge difficulty={prob.difficulty} />
                            </td>
                            <td className="px-6 py-4 text-xs text-gray-400">
                              <span>{prob.attempted_count ?? 0} attempted</span>
                              <span className="mx-1.5 text-gray-600">·</span>
                              <span className="text-emerald-400 font-medium">
                                {prob.accepted_count ?? 0} solved
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <Link
                                href={`/contest/${contest.id}/problem/${prob.problem_id}`}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <button className="bg-surface-border hover:bg-muted text-gray-200 text-xs font-bold px-3 py-1.5 rounded-md transition-colors">
                                  Solve
                                </button>
                              </Link>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-gray-500">
                  No problems found in this contest.
                </div>
              )}
            </div>
          )}

          {activeTab === 'leaderboard' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-400">
                  Rankings update in real-time. Penalty is calculated as 5
                  minutes per wrong submission before solve.
                </div>
                <button
                  onClick={() => refreshLeaderboard()}
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  <RefreshCw className="size-3.5" /> Refresh
                </button>
              </div>

              {isLeaderboardLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <div
                      key={n}
                      className="h-12 bg-surface-dark border border-surface-border rounded-lg animate-pulse"
                    />
                  ))}
                </div>
              ) : leaderboardData?.leaderboard &&
                leaderboardData.leaderboard.length > 0 ? (
                <div className="bg-surface-dark border border-surface-border rounded-xl overflow-x-auto shadow-lg">
                  <table className="w-full text-left border-collapse min-w-[600px]">
                    <thead className="bg-background-dark/60 text-gray-400 text-xs uppercase tracking-wider border-b border-surface-border">
                      <tr>
                        <th className="px-5 py-3 font-medium w-16 text-center">
                          Rank
                        </th>
                        <th className="px-5 py-3 font-medium">User</th>
                        <th className="px-5 py-3 font-medium text-center">
                          Score
                        </th>
                        <th className="px-5 py-3 font-medium text-center">
                          Finish Time
                        </th>
                        <th className="px-5 py-3 font-medium text-center">
                          Solved
                        </th>
                        {contest.problems?.map((p) => (
                          <th
                            key={p.order}
                            className="px-4 py-3 font-medium text-center"
                          >
                            Q{p.order} ({p.points})
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-border text-xs">
                      {leaderboardData.leaderboard.map((entry, idx) => {
                        const isCurrentUser = user && entry.user_id === user.id
                        return (
                          <tr
                            key={entry.user_id}
                            className={`transition-colors ${
                              isCurrentUser
                                ? 'bg-primary/10 hover:bg-primary/15 font-bold'
                                : 'hover:bg-white/5'
                            }`}
                          >
                            <td className="px-5 py-3.5 text-center font-bold">
                              <span
                                className={`inline-block px-2 py-0.5 rounded ${
                                  entry.rank === 1
                                    ? 'bg-yellow-500/20 text-yellow-400 font-black'
                                    : entry.rank === 2
                                      ? 'bg-slate-300/20 text-slate-300 font-bold'
                                      : entry.rank === 3
                                        ? 'bg-amber-600/20 text-amber-500 font-bold'
                                        : 'text-gray-400'
                                }`}
                              >
                                #{entry.rank || idx + 1}
                              </span>
                            </td>
                            <td className="px-5 py-3.5">
                              <div className="flex items-center gap-2.5">
                                <Avatar className="size-7 border border-surface-border">
                                  <AvatarImage src={entry.profile_picture} />
                                  <AvatarFallback>
                                    {entry.username
                                      .substring(0, 2)
                                      .toUpperCase()}
                                  </AvatarFallback>
                                </Avatar>
                                <span className="text-gray-200 font-semibold truncate max-w-[150px]">
                                  {entry.name || entry.username}
                                  {isCurrentUser && (
                                    <span className="text-[10px] text-primary ml-1.5">
                                      (You)
                                    </span>
                                  )}
                                </span>
                              </div>
                            </td>
                            <td className="px-5 py-3.5 text-center font-extrabold text-primary text-sm">
                              {entry.score}
                            </td>
                            <td className="px-5 py-3.5 text-center font-mono text-gray-300">
                              {formatSeconds(entry.finish_time_seconds)}
                              {entry.penalty_seconds >
                                entry.finish_time_seconds && (
                                <span className="text-[10px] text-red-400 block">
                                  +
                                  {Math.floor(
                                    (entry.penalty_seconds -
                                      entry.finish_time_seconds) /
                                      60
                                  )}
                                  m pen
                                </span>
                              )}
                            </td>
                            <td className="px-5 py-3.5 text-center text-emerald-400 font-bold">
                              {entry.problems_solved} /{' '}
                              {contest.problems?.length || 4}
                            </td>
                            {contest.problems?.map((p) => {
                              const pStat =
                                entry.problem_details?.[String(p.problem_id)]
                              const isAC = pStat?.status === 'AC'
                              return (
                                <td
                                  key={p.order}
                                  className="px-4 py-3.5 text-center font-mono"
                                >
                                  {isAC ? (
                                    <div className="text-green-500 font-bold">
                                      +{pStat.points}
                                      <span className="text-[10px] text-gray-500 block">
                                        {formatSeconds(pStat.time_seconds)}
                                      </span>
                                    </div>
                                  ) : pStat?.wrong_attempts ? (
                                    <span className="text-red-500 font-bold text-[11px]">
                                      -{pStat.wrong_attempts}
                                    </span>
                                  ) : (
                                    <span className="text-gray-600">-</span>
                                  )}
                                </td>
                              )
                            })}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-gray-500 bg-surface-dark border border-surface-border rounded-xl">
                  No submissions yet on this contest leaderboard.
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </PageTransition>
  )
}

function ContestCountdown({ contest }: { contest: Contest }) {
  const [timeLeft, setTimeLeft] = useState<{
    days: number
    hours: number
    minutes: number
    seconds: number
    isLive: boolean
  }>({ days: 0, hours: 0, minutes: 0, seconds: 0, isLive: false })

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date().getTime()
      const targetTime =
        contest.status === 'ONGOING'
          ? new Date(contest.end_time).getTime()
          : new Date(contest.start_time).getTime()

      const diff = targetTime - now
      if (diff <= 0) {
        setTimeLeft({
          days: 0,
          hours: 0,
          minutes: 0,
          seconds: 0,
          isLive: contest.status === 'ONGOING',
        })
        return
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      const hours = Math.floor(
        (diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
      )
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      const seconds = Math.floor((diff % (1000 * 60)) / 1000)

      setTimeLeft({
        days,
        hours,
        minutes,
        seconds,
        isLive: contest.status === 'ONGOING',
      })
    }

    updateCountdown()
    const timer = setInterval(updateCountdown, 1000)
    return () => clearInterval(timer)
  }, [contest])

  const isLive = contest.status === 'ONGOING'

  return (
    <div className="text-center sm:text-right">
      <span className="text-xs text-gray-400 font-medium block mb-1">
        {isLive ? 'Time Left' : 'Starts In'}
      </span>
      <div className="flex items-center gap-1.5 text-white font-mono text-lg font-bold">
        {!isLive && timeLeft.days > 0 && <span>{timeLeft.days}d </span>}
        <span className="bg-surface-dark px-2 py-0.5 rounded border border-surface-border">
          {String(timeLeft.hours).padStart(2, '0')}
        </span>
        :
        <span className="bg-surface-dark px-2 py-0.5 rounded border border-surface-border">
          {String(timeLeft.minutes).padStart(2, '0')}
        </span>
        :
        <span className="bg-surface-dark px-2 py-0.5 rounded border border-surface-border text-primary">
          {String(timeLeft.seconds).padStart(2, '0')}
        </span>
      </div>
    </div>
  )
}

function formatSeconds(secs?: number) {
  if (!secs) return '00:00'
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
