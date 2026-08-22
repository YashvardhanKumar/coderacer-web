'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/header'
import PageTransition from '@/components/page-transition'
import { Contest, ContestLeaderboardResponse } from '@/lib/models'
import { apiFetch, apiFetcher, formatInUserTimezone } from '@/lib/utils'
import useSWR, { mutate } from 'swr'
import Link from 'next/link'
import { useAuth } from '@/components/auth-provider'
import { toast } from 'sonner'
import {
  Trophy,
  Calendar,
  Clock,
  Users,
  ChevronRight,
  Sparkles,
  CheckCircle,
  Timer,
  Award,
  Flame,
  ArrowRight,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

export default function ContestIndexPage() {
  const { user } = useAuth()
  const [filterType, setFilterType] = useState<'all' | 'weekly' | 'custom'>(
    'all'
  )
  const [filterStatus, setFilterStatus] = useState<
    'all' | 'upcoming' | 'ongoing' | 'past'
  >('all')

  const query = new URLSearchParams({
    ...(filterType !== 'all' && { type: filterType }),
    ...(filterStatus !== 'all' && { status: filterStatus }),
  }).toString()
  const queryString = query ? `?${query}` : ''

  const { data: contests, isLoading } = useSWR<Contest[]>(
    `contests/${queryString}`,
    apiFetcher
  )

  // Find the primary featured contest (ongoing first, else next upcoming)
  const featuredContest =
    contests?.find((c) => c.status === 'ONGOING') ||
    contests?.find((c) => c.status === 'UPCOMING') ||
    contests?.[0]

  // Get leaderboard for the latest past or ongoing contest
  const latestContestWithLeaderboard =
    contests?.find((c) => c.status === 'ONGOING' || c.status === 'PAST') ||
    featuredContest

  const { data: leaderboardData } = useSWR<ContestLeaderboardResponse>(
    latestContestWithLeaderboard
      ? `contests/${latestContestWithLeaderboard.id}/leaderboard/`
      : null,
    apiFetcher
  )

  const handleRegister = async (contestId: number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!user) {
      toast.error('Please sign in to register for the contest')
      return
    }

    try {
      const res = await apiFetch(`contests/${contestId}/register/`, {
        method: 'POST',
      })
      if (res.ok) {
        toast.success('Successfully registered for the contest!')
        mutate(`contests/${queryString}`)
      } else {
        const data = await res.json()
        toast.error(data.error || 'Failed to register')
      }
    } catch (err: any) {
      toast.error(err.message || 'Error registering')
    }
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-background-dark text-white flex flex-col">
        <Header />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Hero Banner for Featured Contest */}
          {featuredContest && (
            <FeaturedContestBanner
              contest={featuredContest}
              onRegister={(e) => handleRegister(featuredContest.id, e)}
            />
          )}

          {/* Main Layout: Contests List + Leaderboard Sidebar */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-10">
            {/* Left 2 Cols: Contests Filters & List */}
            <div className="lg:col-span-2 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-4">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <Trophy className="text-yellow-500 size-5" />
                    Contests
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Weekly contests every Saturday, plus special rated rounds
                  </p>
                </div>

                <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
                  <div className="bg-surface-dark border border-surface-border p-1 rounded-lg flex text-xs">
                    <button
                      onClick={() => setFilterType('all')}
                      className={`px-3 py-1 rounded-md transition-colors ${
                        filterType === 'all'
                          ? 'bg-primary text-white font-bold'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      All
                    </button>
                    <button
                      onClick={() => setFilterType('weekly')}
                      className={`px-3 py-1 rounded-md transition-colors ${
                        filterType === 'weekly'
                          ? 'bg-primary text-white font-bold'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Weekly Runs
                    </button>
                    <button
                      onClick={() => setFilterType('custom')}
                      className={`px-3 py-1 rounded-md transition-colors ${
                        filterType === 'custom'
                          ? 'bg-primary text-white font-bold'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Custom
                    </button>
                  </div>

                  <div className="bg-surface-dark border border-surface-border p-1 rounded-lg flex text-xs">
                    <button
                      onClick={() => setFilterStatus('all')}
                      className={`px-2.5 py-1 rounded-md transition-colors ${
                        filterStatus === 'all'
                          ? 'bg-surface-border text-white font-bold'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      All
                    </button>
                    <button
                      onClick={() => setFilterStatus('upcoming')}
                      className={`px-2.5 py-1 rounded-md transition-colors ${
                        filterStatus === 'upcoming'
                          ? 'bg-surface-border text-white font-bold'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Upcoming
                    </button>
                    <button
                      onClick={() => setFilterStatus('past')}
                      className={`px-2.5 py-1 rounded-md transition-colors ${
                        filterStatus === 'past'
                          ? 'bg-surface-border text-white font-bold'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Past
                    </button>
                  </div>
                </div>
              </div>

              {/* Contests Grid */}
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((n) => (
                    <div
                      key={n}
                      className="h-28 bg-surface-dark/50 border border-surface-border rounded-xl animate-pulse"
                    />
                  ))}
                </div>
              ) : contests && contests.length > 0 ? (
                <div className="space-y-4">
                  {contests.map((contest) => (
                    <ContestCard
                      key={contest.id}
                      contest={contest}
                      onRegister={(e) => handleRegister(contest.id, e)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-surface-dark/30 border border-surface-border rounded-xl">
                  <Trophy className="size-12 text-gray-600 mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-gray-300">
                    No Contests Found
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Check back soon for the next scheduled Weekly Run!
                  </p>
                </div>
              )}
            </div>

            {/* Right 1 Col: Leaderboard Preview & Rules */}
            <div className="space-y-6">
              {/* Leaderboard Card */}
              <div className="bg-surface-dark border border-surface-border rounded-xl p-5 shadow-lg">
                <div className="flex items-center justify-between border-b border-surface-border pb-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Award className="text-yellow-400 size-5" />
                    <h3 className="font-bold text-sm text-white">
                      {latestContestWithLeaderboard
                        ? `${latestContestWithLeaderboard.title} Leaderboard`
                        : 'Contest Leaderboard'}
                    </h3>
                  </div>
                  {latestContestWithLeaderboard && (
                    <Link
                      href={`/contest/${latestContestWithLeaderboard.id}`}
                      className="text-xs text-primary hover:underline flex items-center"
                    >
                      Full Board <ChevronRight className="size-3" />
                    </Link>
                  )}
                </div>

                {leaderboardData?.leaderboard &&
                leaderboardData.leaderboard.length > 0 ? (
                  <div className="space-y-2.5">
                    {leaderboardData.leaderboard
                      .slice(0, 7)
                      .map((entry, idx) => (
                        <div
                          key={entry.user_id}
                          className="flex items-center justify-between p-2 rounded-lg bg-background-dark/50 hover:bg-background-dark transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <span
                              className={`w-5 text-center font-bold text-xs ${
                                idx === 0
                                  ? 'text-yellow-400 font-extrabold text-sm'
                                  : idx === 1
                                    ? 'text-slate-300 text-sm font-bold'
                                    : idx === 2
                                      ? 'text-amber-600 text-sm font-bold'
                                      : 'text-gray-500'
                              }`}
                            >
                              {entry.rank || idx + 1}
                            </span>
                            <Avatar className="size-7 border border-surface-border">
                              <AvatarImage src={entry.profile_picture} />
                              <AvatarFallback>
                                {entry.username.substring(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <span className="text-xs font-semibold text-gray-200 truncate max-w-[110px]">
                              {entry.name || entry.username}
                            </span>
                          </div>
                          <div className="text-right">
                            <span className="text-xs font-bold text-primary">
                              {entry.score} pts
                            </span>
                            <div className="text-[10px] text-gray-500 font-mono">
                              {Math.floor(entry.penalty_seconds / 60)}m
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="py-8 text-center text-xs text-gray-500">
                    No leaderboard data available yet.
                  </div>
                )}
              </div>

              {/* Contest Rules & Information Card */}
              <div className="bg-surface-dark border border-surface-border rounded-xl p-5 text-xs text-gray-400 space-y-3">
                <h4 className="font-bold text-white text-sm flex items-center gap-1.5">
                  <Sparkles className="size-4 text-primary" />
                  Contest Rules & Format
                </h4>
                <ul className="space-y-2 list-disc list-inside text-gray-400 leading-relaxed">
                  <li>
                    <b className="text-gray-300">Points & Hardness:</b> Each
                    problem has score points based on difficulty (Easy: 3,
                    Medium: 5, Hard: 7).
                  </li>
                  <li>
                    <b className="text-gray-300">Penalty Time:</b> Every wrong
                    submission before an Accepted solution adds a 5-minute
                    penalty.
                  </li>
                  <li>
                    <b className="text-gray-300">Contest Mode:</b> Discussion,
                    solutions, editorials, and testcase pass/fail verdicts are
                    hidden during contest.
                  </li>
                  <li>
                    <b className="text-gray-300">Weekly Run:</b> Official
                    contests take place every Saturday at 8:00 PM.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </PageTransition>
  )
}

function FeaturedContestBanner({
  contest,
  onRegister,
}: {
  contest: Contest
  onRegister: (e: React.MouseEvent) => void
}) {
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
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 border border-blue-800/40 p-6 sm:p-8 shadow-2xl">
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-primary/20 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-3 max-w-xl">
          <div className="flex items-center gap-2">
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                isLive
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse'
                  : 'bg-primary/20 text-primary border border-primary/30'
              }`}
            >
              {isLive
                ? '● Live Now'
                : contest.is_weekly
                  ? 'Official Weekly Run'
                  : 'Special Contest'}
            </span>
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Clock className="size-3.5" />
              {contest.duration_minutes} Minutes
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {contest.title}
          </h1>

          <p className="text-xs sm:text-sm text-gray-300 line-clamp-2">
            {contest.description ||
              'Compete against programmers worldwide! Solve fresh algorithmic problems, earn points based on hardness, and climb the live leaderboard.'}
          </p>

          <div className="flex items-center gap-4 text-xs text-gray-400 pt-1">
            <div className="flex items-center gap-1.5">
              <Calendar className="size-4 text-primary" />
              {formatInUserTimezone(
                contest.start_time,
                'EEE, MMM d, yyyy · HH:mm'
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <Users className="size-4 text-primary" />
              {contest.registered_count} Registered
            </div>
          </div>
        </div>

        {/* Countdown & CTA */}
        <div className="flex flex-col items-center md:items-end gap-4 w-full md:w-auto bg-black/40 p-5 rounded-xl border border-white/5 backdrop-blur-sm">
          <div className="text-center md:text-right">
            <span className="text-xs text-gray-400 font-medium block mb-1.5">
              {isLive ? 'Time Remaining in Contest' : 'Contest Starts In'}
            </span>
            <div className="flex items-center gap-2 text-white font-mono">
              {!isLive && timeLeft.days > 0 && (
                <div className="flex flex-col items-center bg-surface-dark px-2.5 py-1.5 rounded-md border border-surface-border">
                  <span className="text-xl font-bold">{timeLeft.days}</span>
                  <span className="text-[9px] text-gray-400 uppercase">
                    Days
                  </span>
                </div>
              )}
              <div className="flex flex-col items-center bg-surface-dark px-2.5 py-1.5 rounded-md border border-surface-border">
                <span className="text-xl font-bold">
                  {String(timeLeft.hours).padStart(2, '0')}
                </span>
                <span className="text-[9px] text-gray-400 uppercase">
                  Hours
                </span>
              </div>
              <span className="text-lg text-gray-500 font-bold">:</span>
              <div className="flex flex-col items-center bg-surface-dark px-2.5 py-1.5 rounded-md border border-surface-border">
                <span className="text-xl font-bold">
                  {String(timeLeft.minutes).padStart(2, '0')}
                </span>
                <span className="text-[9px] text-gray-400 uppercase">Mins</span>
              </div>
              <span className="text-lg text-gray-500 font-bold">:</span>
              <div className="flex flex-col items-center bg-surface-dark px-2.5 py-1.5 rounded-md border border-surface-border">
                <span className="text-xl font-bold text-primary">
                  {String(timeLeft.seconds).padStart(2, '0')}
                </span>
                <span className="text-[9px] text-gray-400 uppercase">Secs</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {isLive ? (
              <Link
                href={`/contest/${contest.id}`}
                className="w-full sm:w-auto"
              >
                <button className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-2.5 rounded-lg text-sm transition-all shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2">
                  <Flame className="size-4 animate-bounce" />
                  Enter Live Contest
                </button>
              </Link>
            ) : contest.is_registered ? (
              <Link
                href={`/contest/${contest.id}`}
                className="w-full sm:w-auto"
              >
                <button className="w-full sm:w-auto bg-surface-border hover:bg-muted text-emerald-400 font-bold px-5 py-2.5 rounded-lg text-sm transition-all flex items-center justify-center gap-2 border border-emerald-500/30">
                  <CheckCircle className="size-4" />
                  Registered (View Lobby)
                </button>
              </Link>
            ) : (
              <button
                onClick={onRegister}
                className="w-full sm:w-auto bg-primary hover:bg-primary/90 text-white font-bold px-6 py-2.5 rounded-lg text-sm transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
              >
                Register Now
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ContestCard({
  contest,
  onRegister,
}: {
  contest: Contest
  onRegister: (e: React.MouseEvent) => void
}) {
  const isLive = contest.status === 'ONGOING'
  const isUpcoming = contest.status === 'UPCOMING'
  const isPast = contest.status === 'PAST'

  return (
    <Link href={`/contest/${contest.id}`}>
      <div className="bg-surface-dark border border-surface-border hover:border-primary/50 transition-all rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group cursor-pointer">
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                contest.is_weekly
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'bg-slate-700 text-gray-300'
              }`}
            >
              {contest.is_weekly ? 'WEEKLY RUN' : 'CUSTOM'}
            </span>

            {isLive && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse">
                ● Live Now
              </span>
            )}
            {isUpcoming && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Upcoming
              </span>
            )}
            {isPast && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-gray-800 text-gray-400">
                Past Contest
              </span>
            )}
          </div>

          <h3 className="text-base font-bold text-white group-hover:text-primary transition-colors flex items-center gap-2">
            {contest.title}
          </h3>

          <div className="flex items-center gap-4 text-xs text-gray-400 flex-wrap">
            <span className="flex items-center gap-1">
              <Calendar className="size-3.5 text-gray-500" />
              {formatInUserTimezone(contest.start_time, 'MMM d, yyyy · HH:mm')}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="size-3.5 text-gray-500" />
              {contest.duration_minutes} mins
            </span>
            <span className="flex items-center gap-1">
              <Users className="size-3.5 text-gray-500" />
              {contest.registered_count} participants
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          {isLive ? (
            <button className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors flex items-center gap-1">
              Solve Problems <ArrowRight className="size-3.5" />
            </button>
          ) : isUpcoming ? (
            contest.is_registered ? (
              <span className="text-emerald-400 font-bold text-xs flex items-center gap-1 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
                <CheckCircle className="size-3.5" /> Registered
              </span>
            ) : (
              <button
                onClick={onRegister}
                className="bg-primary hover:bg-primary/90 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors"
              >
                Register
              </button>
            )
          ) : (
            <span className="text-gray-400 text-xs font-semibold flex items-center gap-1">
              View Results <ChevronRight className="size-4" />
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
