'use client'

import { useEffect, useMemo, useState } from 'react'
import Header from '@/components/header'
import PageTransition from '@/components/page-transition'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiFetcher, formatInUserTimezone } from '@/lib/utils'
import apiClient from '@/lib/utils'
import {
  Difficulty,
  HeatmapDay,
  Language,
  LanguageDisplayNames,
  ProfileProblemSummary,
  ProfileSubmission,
  ProfileProblemDiscussion,
  ProfileGeneralDiscussion,
  Status,
  UserProfile,
} from '@/lib/models'
import { format, parseISO } from 'date-fns'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import useSWR, { mutate } from 'swr'
import { toast } from 'sonner'
import { useAuth } from '@/components/auth-provider'
import { Skeleton } from '@/components/ui/skeleton'
import {
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Eye,
  CheckCircle2,
  Clock,
  Code2,
  FileCode2,
  FileText,
  Pin,
  Sparkles,
  ExternalLink,
  Star,
} from 'lucide-react'

const difficultyColors: Record<Difficulty, string> = {
  [Difficulty.EASY]: 'text-green-500 bg-green-500/10',
  [Difficulty.MEDIUM]: 'text-yellow-500 bg-yellow-500/10',
  [Difficulty.HARD]: 'text-red-500 bg-red-500/10',
}

const heatLevels = [
  'bg-slate-100 dark:bg-slate-800',
  'bg-emerald-200 dark:bg-emerald-900',
  'bg-emerald-300 dark:bg-emerald-700',
  'bg-emerald-500 dark:bg-emerald-500',
  'bg-emerald-700 dark:bg-emerald-300',
]

export default function ProfilePage() {
  const router = useRouter()
  const { user, loading, refreshUser } = useAuth()
  const [selectedYear, setSelectedYear] = useState<number>(
    new Date().getFullYear()
  )

  const { data, error, isLoading } = useSWR<UserProfile>(
    user ? `auth/users/profile/?year=${selectedYear}` : null,
    apiFetcher
  )
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [defaultLang, setDefaultLang] = useState<Language>(Language.PYTHON)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [loading, router, user])

  useEffect(() => {
    if (!data?.user) return
    setName(data.user.name ?? '')
    setEmail(data.user.email ?? '')
    setDefaultLang(data.user.default_lang ?? Language.PYTHON)
  }, [data?.user])

  const avatarUrl =
    data?.user.profile_picture_url ||
    `https://api.dicebear.com/7.x/avataaars/svg?seed=${data?.user.username || 'codeflip'}`
  const displayName = data?.user.name || data?.user.username || 'CodeFlip'
  const statuses = data
    ? Object.entries(data.stats.status_breakdown).filter(
        ([, count]) => count > 0
      )
    : []

  const saveProfile = async () => {
    setIsSaving(true)
    try {
      await apiClient.patch('auth/users/update_profile/', {
        name,
        email,
        default_lang: defaultLang,
      })
      await Promise.all([mutate('auth/users/profile/'), refreshUser()])
      toast.success('Profile updated')
    } catch {
      toast.error('Could not update profile')
    } finally {
      setIsSaving(false)
    }
  }

  const uploadProfilePicture = async (file?: File) => {
    if (!file) return
    const formData = new FormData()
    formData.append('profile_picture', file)

    try {
      await apiClient.patch('auth/users/update_profile/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      await Promise.all([mutate('auth/users/profile/'), refreshUser()])
      toast.success('Profile picture updated')
    } catch {
      toast.error('Could not upload profile picture')
    }
  }

  const showLoading = loading || isLoading

  if (error && !showLoading) {
    const isAuthError =
      error?.response?.status === 401 || error?.status === 401 || !user

    return (
      <div className="min-h-screen bg-background-light dark:bg-background-dark text-slate-900 dark:text-white flex flex-col font-sans">
        <Header />
        <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-md mx-auto">
          <div className="size-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-4">
            <Sparkles className="size-8" />
          </div>
          <h2 className="text-xl font-bold mb-2">
            {isAuthError ? 'Authentication Required' : 'Unable to Load Profile'}
          </h2>
          <p className="text-sm text-slate-500 dark:text-text-secondary mb-6 leading-relaxed">
            {isAuthError
              ? 'Your session may have expired. Please sign in to view and manage your profile statistics.'
              : error?.message ||
                'A network error occurred while fetching your profile.'}
          </p>
          <div className="flex gap-3">
            {isAuthError ? (
              <Link href="/login">
                <Button className="bg-primary hover:bg-primary/90 text-white font-bold px-6 py-2 rounded-xl text-xs shadow-md">
                  Sign In to Account
                </Button>
              </Link>
            ) : (
              <Button
                onClick={() =>
                  mutate(`auth/users/profile/?year=${selectedYear}`)
                }
                className="bg-primary hover:bg-primary/90 text-white font-bold px-6 py-2 rounded-xl text-xs shadow-md"
              >
                Retry Loading
              </Button>
            )}
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark">
      <Header />
      <PageTransition>
        <main className="mx-auto flex max-w-350 flex-col gap-6 p-4 md:p-8">
          <section className="grid gap-6 lg:grid-cols-[320px_1fr]">
            {/* Left Sidebar Profile Info */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-surface-border dark:bg-surface-dark">
              {showLoading ? (
                <div className="space-y-6">
                  <div className="flex flex-col items-center gap-4">
                    <Skeleton className="size-28 rounded-full" />
                    <Skeleton className="h-8 w-32 rounded-md" />
                  </div>
                  <div className="grid grid-cols-2 gap-3 mt-6">
                    {[1, 2, 3, 4].map((i) => (
                      <Skeleton key={i} className="h-16 w-full rounded-md" />
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center text-center">
                  <Avatar className="size-28 border border-slate-200 dark:border-surface-border">
                    <AvatarImage src={avatarUrl} />
                    <AvatarFallback>
                      {data?.user.username.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <Label
                    htmlFor="profile-picture"
                    className="mt-4 cursor-pointer rounded-md bg-primary px-3 py-2 text-xs font-bold text-white hover:bg-primary/90"
                  >
                    Change Photo
                  </Label>
                  <input
                    id="profile-picture"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(event) =>
                      uploadProfilePicture(event.target.files?.[0])
                    }
                  />
                  <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">
                    {displayName}
                  </h1>
                  <p className="text-sm text-slate-500 dark:text-text-secondary">
                    @{data?.user.username}
                  </p>
                  <p className="mt-2 text-xs text-slate-500 dark:text-text-secondary">
                    Joined{' '}
                    {formatInUserTimezone(
                      data?.user.date_joined || '',
                      'MMM d, yyyy'
                    )}
                  </p>
                </div>
              )}

              {!showLoading && (
                <>
                  <div className="mt-6 grid grid-cols-2 gap-3">
                    <StatTile
                      label="Solved"
                      value={data?.stats.unique_problems_solved || 0}
                    />
                    <StatTile
                      label="Attempts"
                      value={data?.stats.total_submissions || 0}
                    />
                    <StatTile
                      label="Streak"
                      value={`${data?.stats.current_streak || 0}d`}
                    />
                    <StatTile
                      label="Active Days"
                      value={data?.stats.active_days || 0}
                    />
                  </div>
                  <div className="mt-6">
                    {statuses.length === 0 ? (
                      <p className="text-sm text-slate-500 dark:text-text-secondary">
                        No submission statuses yet.
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {statuses.slice(0, 2).map(([status, count]) => (
                          <div
                            key={status}
                            className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 dark:bg-background-dark"
                          >
                            <span className="text-sm text-slate-600 dark:text-text-secondary">
                              {status}
                            </span>
                            <span className="font-bold text-slate-900 dark:text-white">
                              {count}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="mt-6 space-y-3">
                    <ProfileField
                      label="Name"
                      value={name}
                      onChange={setName}
                    />
                    <ProfileField
                      label="Email"
                      value={email}
                      onChange={setEmail}
                    />
                    <div className="space-y-1.5">
                      <Label>Default language</Label>
                      <select
                        value={defaultLang}
                        onChange={(event) =>
                          setDefaultLang(event.target.value as Language)
                        }
                        className="h-9 w-full rounded-md border border-slate-200 bg-transparent px-3 text-sm dark:border-surface-border"
                      >
                        {Object.values(Language).map((language) => (
                          <option key={language} value={language}>
                            {LanguageDisplayNames[language]}
                          </option>
                        ))}
                      </select>
                    </div>
                    <Button
                      onClick={saveProfile}
                      disabled={isSaving}
                      className="w-full bg-primary text-white hover:bg-primary/90"
                    >
                      {isSaving ? 'Saving...' : 'Save Profile'}
                    </Button>
                  </div>
                </>
              )}
            </div>

            {/* Right Column: Progress, Heatmap, Merged Submissions Card & Merged Discussions Card */}
            <div className="flex flex-col gap-6">
              {/* Progress Card */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-surface-border dark:bg-surface-dark">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                      Progress
                    </h2>
                    <div className="text-sm text-slate-500 dark:text-text-secondary">
                      {showLoading ? (
                        <Skeleton className="h-4 w-36" />
                      ) : (
                        `${data?.stats.success_rate || 0}% accepted across ${data?.stats.total_submissions || 0} submissions`
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-slate-500 dark:text-text-secondary">
                    {showLoading ? (
                      <Skeleton className="h-4 w-24" />
                    ) : (
                      `${data?.stats.unique_problems_attempted || 0} problems attempted`
                    )}
                  </div>
                </div>
                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  {Object.values(Difficulty).map((difficulty) => (
                    <DifficultyProgress
                      key={difficulty}
                      difficulty={difficulty}
                      data={data}
                      isLoading={showLoading}
                    />
                  ))}
                </div>
              </section>

              {/* Heatmap Card */}
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-surface-border dark:bg-surface-dark">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                      Submission Heatmap
                    </h2>
                    <p className="text-sm text-slate-500 dark:text-text-secondary">
                      Coding activity for{' '}
                      {showLoading ? '...' : data?.selected_year}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <select
                      value={selectedYear}
                      onChange={(e) => setSelectedYear(Number(e.target.value))}
                      className="h-8 rounded-md border border-slate-200 bg-transparent px-2 text-xs font-medium dark:border-surface-border"
                    >
                      {showLoading ? (
                        <option>...</option>
                      ) : (
                        data?.available_years?.map((y) => (
                          <option key={y} value={y}>
                            {y}
                          </option>
                        ))
                      )}
                    </select>
                    <span className="text-xs text-slate-500 dark:text-text-secondary">
                      {showLoading ? (
                        <Skeleton className="h-4 w-16" />
                      ) : (
                        `${data?.stats?.active_days || 0} active days`
                      )}
                    </span>
                  </div>
                </div>
                {showLoading ? (
                  <Skeleton className="h-32 w-full" />
                ) : (
                  <Heatmap days={data?.heatmap || []} />
                )}
              </section>

              {/* 2 Tabbed Cards Side-by-Side:
                  1. Merged Problems & Submissions Card (Submissions, Solved, Attempted)
                  2. Merged Discussions Card (Problem Solutions/Discussions, General Discussions)
              */}
              <section className="grid gap-6 xl:grid-cols-2">
                {/* Merged Problems & Submissions Card */}
                <SubmissionsTabCard
                  submissions={data?.recent_submissions}
                  solvedProblems={data?.solved_problems}
                  attemptedProblems={data?.attempted_problems}
                  favoriteProblems={data?.favorite_problems}
                  isLoading={showLoading}
                />

                {/* Merged Discussions Card */}
                <DiscussionsTabCard
                  problemDiscussions={data?.problem_discussions}
                  generalDiscussions={data?.general_discussions}
                  isLoading={showLoading}
                />
              </section>
            </div>
          </section>
        </main>
      </PageTransition>
    </div>
  )
}

function ProfileField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  )
}

function StatTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3 dark:bg-background-dark border border-slate-100 dark:border-surface-border">
      <div className="text-xl font-bold text-slate-900 dark:text-white">
        {value}
      </div>
      <div className="text-xs text-slate-500 dark:text-text-secondary">
        {label}
      </div>
    </div>
  )
}

function DifficultyProgress({
  difficulty,
  data,
  isLoading,
}: {
  difficulty: Difficulty
  data: UserProfile | undefined
  isLoading: boolean
}) {
  if (isLoading || !data) return <Skeleton className="h-24 w-full rounded-xl" />

  const stats = data.stats.difficulty_breakdown[difficulty]
  const attempted = Math.max(stats.attempted, stats.solved)
  const percentage =
    attempted === 0 ? 0 : Math.round((stats.solved / attempted) * 100)

  return (
    <div className="rounded-xl bg-slate-50 p-4 dark:bg-background-dark border border-slate-100 dark:border-surface-border">
      <div className="flex items-center justify-between">
        <span
          className={`rounded-md px-2 py-1 text-xs font-bold ${difficultyColors[difficulty]}`}
        >
          {difficulty}
        </span>
        <span className="text-sm font-semibold">
          {stats.solved}/{attempted}
        </span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

function Heatmap({ days }: { days: HeatmapDay[] }) {
  const months = useMemo(() => {
    const grouped: Record<string, HeatmapDay[]> = {}
    days.forEach((day) => {
      const monthKey = format(parseISO(day.date), 'MMM')
      if (!grouped[monthKey]) grouped[monthKey] = []
      grouped[monthKey].push(day)
    })
    return Object.entries(grouped)
  }, [days])

  return (
    <div className="overflow-x-auto pb-2">
      <div className="flex min-w-max gap-6">
        {months.map(([month, monthDays]) => {
          const weeks: HeatmapDay[][] = []
          for (let i = 0; i < monthDays.length; i += 7) {
            weeks.push(monthDays.slice(i, i + 7))
          }

          return (
            <div key={month} className="flex flex-col gap-2">
              <span className="text-[10px] font-medium text-slate-400 dark:text-text-secondary uppercase tracking-wider">
                {month}
              </span>
              <div className="flex gap-1">
                {weeks.map((week, weekIndex) => (
                  <div key={weekIndex} className="grid grid-rows-7 gap-1">
                    {week.map((day) => {
                      const level = Math.min(day.count, heatLevels.length - 1)
                      return (
                        <div
                          key={day.date}
                          title={`${day.date}: ${day.count} submissions`}
                          className={`size-3 rounded-xs ${heatLevels[level]} transition-colors hover:ring-1 hover:ring-primary/50`}
                        />
                      )
                    })}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
      <div className="mt-4 flex items-center gap-2 text-[10px] text-slate-400">
        <span>Less</span>
        {heatLevels.map((level, i) => (
          <div key={i} className={`size-3 rounded-xs ${level}`} />
        ))}
        <span>More</span>
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------
// MERGED CARD 1: Problems & Submissions Activity (3 Tabs)
// ----------------------------------------------------------------------------
function SubmissionsTabCard({
  submissions,
  solvedProblems,
  attemptedProblems,
  favoriteProblems,
  isLoading,
}: {
  submissions?: ProfileSubmission[]
  solvedProblems?: ProfileProblemSummary[]
  attemptedProblems?: ProfileProblemSummary[]
  favoriteProblems?: ProfileProblemSummary[]
  isLoading: boolean
}) {
  const [activeTab, setActiveTab] = useState<
    'submissions' | 'solved' | 'attempted' | 'favorites'
  >('submissions')

  return (
    <div className="rounded-2xl border border-slate-200 bg-white dark:border-surface-border dark:bg-surface-dark h-[440px] flex flex-col shadow-sm overflow-hidden">
      {/* Header & Tabs */}
      <div className="p-5 pb-3 border-b border-slate-100 dark:border-surface-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
            <FileCode2 className="size-4.5 text-primary" />
            <span>Problem Activity</span>
          </h3>
        </div>

        {/* Tab Pills */}
        <div className="flex gap-1 bg-slate-100 dark:bg-background-dark p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('submissions')}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'submissions'
                ? 'bg-white dark:bg-surface-dark text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Clock className="size-3" />
            <span className="hidden sm:inline">Submissions</span>
            <span className="sm:hidden">Subs</span>
            <span className="text-[10px] font-mono opacity-70">
              ({submissions?.length || 0})
            </span>
          </button>

          <button
            onClick={() => setActiveTab('solved')}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'solved'
                ? 'bg-white dark:bg-surface-dark text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <CheckCircle2 className="size-3 text-green-500" />
            <span>Solved</span>
            <span className="text-[10px] font-mono opacity-70">
              ({solvedProblems?.length || 0})
            </span>
          </button>

          <button
            onClick={() => setActiveTab('attempted')}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'attempted'
                ? 'bg-white dark:bg-surface-dark text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Code2 className="size-3 text-amber-500" />
            <span className="hidden sm:inline">Attempted</span>
            <span className="sm:hidden">Att.</span>
            <span className="text-[10px] font-mono opacity-70">
              ({attemptedProblems?.length || 0})
            </span>
          </button>

          <button
            onClick={() => setActiveTab('favorites')}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'favorites'
                ? 'bg-white dark:bg-surface-dark text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Star className="size-3 text-amber-400 fill-amber-400" />
            <span className="hidden sm:inline">Favorites</span>
            <span className="sm:hidden">Favs</span>
            <span className="text-[10px] font-mono opacity-70">
              ({favoriteProblems?.length || 0})
            </span>
          </button>
        </div>
      </div>

      {/* Tab Content List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
        {isLoading ? (
          [1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-14 w-full rounded-xl" />
          ))
        ) : activeTab === 'submissions' ? (
          !submissions || submissions.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 dark:text-text-secondary">
              No recent submissions found.
            </div>
          ) : (
            submissions.map((sub) => (
              <Link
                key={sub.id}
                href={`/problems/${sub.problem_id}?tab=submissions&submissionId=${sub.id}`}
                className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-background-dark/70 dark:hover:bg-background-dark border border-slate-100 dark:border-surface-border transition-colors group"
              >
                <div className="min-w-0">
                  <div className="font-bold text-xs text-slate-900 dark:text-white truncate group-hover:text-primary transition-colors">
                    {sub.problem_name}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-text-secondary mt-0.5">
                    {sub.language_display} ·{' '}
                    {formatInUserTimezone(sub.created_at, 'MMM d, HH:mm')}
                  </div>
                </div>

                <span
                  className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold ${
                    sub.status === Status.SUCCESS
                      ? 'bg-green-500/10 text-green-500'
                      : 'bg-red-500/10 text-red-500'
                  }`}
                >
                  {sub.status_display}
                </span>
              </Link>
            ))
          )
        ) : activeTab === 'solved' ? (
          !solvedProblems || solvedProblems.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 dark:text-text-secondary">
              No solved problems yet. Keep practicing!
            </div>
          ) : (
            solvedProblems.map((prob) => (
              <Link
                key={prob.id}
                href={`/problems/${prob.id}`}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-background-dark/70 dark:hover:bg-background-dark border border-slate-100 dark:border-surface-border transition-colors group"
              >
                <div className="font-bold text-xs text-slate-900 dark:text-white truncate group-hover:text-primary transition-colors">
                  {prob.id}. {prob.name}
                </div>
                <span
                  className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold ${difficultyColors[prob.difficulty]}`}
                >
                  {prob.difficulty}
                </span>
              </Link>
            ))
          )
        ) : activeTab === 'attempted' ? (
          !attemptedProblems || attemptedProblems.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 dark:text-text-secondary">
              No attempted problems pending completion.
            </div>
          ) : (
            attemptedProblems.map((prob) => (
              <Link
                key={prob.id}
                href={`/problems/${prob.id}`}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-background-dark/70 dark:hover:bg-background-dark border border-slate-100 dark:border-surface-border transition-colors group"
              >
                <div className="font-bold text-xs text-slate-900 dark:text-white truncate group-hover:text-primary transition-colors">
                  {prob.id}. {prob.name}
                </div>
                <span
                  className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold ${difficultyColors[prob.difficulty]}`}
                >
                  {prob.difficulty}
                </span>
              </Link>
            ))
          )
        ) : !favoriteProblems || favoriteProblems.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500 dark:text-text-secondary">
            No favorite problems added yet. Click &quot;Add to List&quot; on any
            problem!
          </div>
        ) : (
          favoriteProblems.map((prob) => (
            <Link
              key={prob.id}
              href={`/problems/${prob.id}`}
              className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-background-dark/70 dark:hover:bg-background-dark border border-slate-100 dark:border-surface-border transition-colors group"
            >
              <div className="min-w-0 pr-2">
                <div className="font-bold text-xs text-slate-900 dark:text-white truncate group-hover:text-primary transition-colors">
                  {prob.id}. {prob.name}
                </div>
                {prob.tags && prob.tags.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {prob.tags.slice(0, 3).map((tag, idx) => (
                      <span
                        key={idx}
                        className="text-[9px] text-gray-500 bg-slate-200/50 dark:bg-surface-border/50 px-1.5 py-0.5 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <span
                className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold ${difficultyColors[prob.difficulty]}`}
              >
                {prob.difficulty}
              </span>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------
// MERGED CARD 2: Discussions & Community Activity (2 Tabs)
// ----------------------------------------------------------------------------
function DiscussionsTabCard({
  problemDiscussions,
  generalDiscussions,
  isLoading,
}: {
  problemDiscussions?: ProfileProblemDiscussion[]
  generalDiscussions?: ProfileGeneralDiscussion[]
  isLoading: boolean
}) {
  const [activeTab, setActiveTab] = useState<'problem' | 'general'>('problem')

  return (
    <div className="rounded-2xl border border-slate-200 bg-white dark:border-surface-border dark:bg-surface-dark h-[440px] flex flex-col shadow-sm overflow-hidden">
      {/* Header & Tabs */}
      <div className="p-5 pb-3 border-b border-slate-100 dark:border-surface-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
            <MessageSquare className="size-4.5 text-primary" />
            <span>My Discussions & Solutions</span>
          </h3>
        </div>

        {/* Tab Pills */}
        <div className="flex gap-1 bg-slate-100 dark:bg-background-dark p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('problem')}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'problem'
                ? 'bg-white dark:bg-surface-dark text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <FileText className="size-3" />
            <span>Problem Solutions</span>
            <span className="text-[10px] font-mono opacity-70">
              ({problemDiscussions?.length || 0})
            </span>
          </button>

          <button
            onClick={() => setActiveTab('general')}
            className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'general'
                ? 'bg-white dark:bg-surface-dark text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Sparkles className="size-3 text-primary" />
            <span>General Discuss</span>
            <span className="text-[10px] font-mono opacity-70">
              ({generalDiscussions?.length || 0})
            </span>
          </button>
        </div>
      </div>

      {/* Tab Content List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
        {isLoading ? (
          [1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))
        ) : activeTab === 'problem' ? (
          !problemDiscussions || problemDiscussions.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 dark:text-text-secondary">
              <p>No problem solutions or discussions posted yet.</p>
              <p className="mt-1 text-[11px] opacity-70">
                Submit an accepted solution on any problem and post your
                solution to share with others!
              </p>
            </div>
          ) : (
            problemDiscussions.map((disc) => (
              <Link
                key={disc.id}
                href={`/problems/${disc.problem_id}?tab=solutions&discussionId=${disc.id}`}
                className="block p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-background-dark/70 dark:hover:bg-background-dark border border-slate-100 dark:border-surface-border transition-colors group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-[11px] font-bold text-primary truncate">
                        {disc.problem_name}
                      </span>
                      {disc.is_editorial && (
                        <span className="bg-amber-500/20 text-amber-500 text-[10px] font-bold px-2 py-0.5 rounded-full border border-amber-500/30">
                          Editorial
                        </span>
                      )}
                    </div>
                    <div className="font-medium text-xs text-slate-900 dark:text-white line-clamp-1 group-hover:text-primary transition-colors">
                      {disc.title}
                    </div>
                  </div>

                  {/* Views & Likes/Dislikes */}
                  <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-text-secondary shrink-0 pt-0.5">
                    <span className="flex items-center gap-1">
                      <Eye className="size-3 text-slate-400" />
                      <span>{disc.views}</span>
                    </span>
                    <span className="flex items-center gap-1 text-green-500">
                      <ThumbsUp className="size-3" />
                      <span>{disc.upvotes_count}</span>
                    </span>
                    <span className="flex items-center gap-1 text-rose-400">
                      <ThumbsDown className="size-3" />
                      <span>{disc.downvotes_count}</span>
                    </span>
                  </div>
                </div>

                <div className="text-[10px] text-slate-400 dark:text-text-secondary mt-2 flex items-center justify-between">
                  <span>
                    {formatInUserTimezone(disc.created_at, 'MMM d, yyyy')}
                  </span>
                  <span className="flex items-center gap-1 text-primary group-hover:underline">
                    View Problem <ExternalLink className="size-2.5" />
                  </span>
                </div>
              </Link>
            ))
          )
        ) : !generalDiscussions || generalDiscussions.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500 dark:text-text-secondary">
            <p>No general discussion topics created yet.</p>
            <Link href="/discuss/new" className="inline-block mt-2">
              <span className="text-primary hover:underline text-xs font-bold">
                Create your first discussion topic →
              </span>
            </Link>
          </div>
        ) : (
          generalDiscussions.map((post) => (
            <Link
              key={post.id}
              href={`/discuss/${post.id}`}
              className="block p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-background-dark/70 dark:hover:bg-background-dark border border-slate-100 dark:border-surface-border transition-colors group"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <span className="inline-block bg-primary/10 text-primary text-[10px] font-bold px-2 py-0.5 rounded-full border border-primary/20 mb-1">
                    {post.category_display || post.category}
                  </span>
                  <div className="font-bold text-xs text-slate-900 dark:text-white line-clamp-1 group-hover:text-primary transition-colors">
                    {post.title}
                  </div>
                </div>

                {/* Views & Votes & Comments */}
                <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-text-secondary shrink-0 pt-0.5">
                  <span className="flex items-center gap-1">
                    <Eye className="size-3 text-slate-400" />
                    <span>{post.views}</span>
                  </span>
                  <span className="flex items-center gap-1 text-primary font-bold">
                    <ThumbsUp className="size-3" />
                    <span>{post.vote_count}</span>
                  </span>
                  <span className="flex items-center gap-1 text-slate-400">
                    <MessageSquare className="size-3" />
                    <span>{post.comments_count}</span>
                  </span>
                </div>
              </div>

              <div className="text-[10px] text-slate-400 dark:text-text-secondary mt-2 flex items-center justify-between">
                <span>
                  {formatInUserTimezone(post.created_at, 'MMM d, yyyy')}
                </span>
                <span className="flex items-center gap-1 text-primary group-hover:underline">
                  Read Post <ExternalLink className="size-2.5" />
                </span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
