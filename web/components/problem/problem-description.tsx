import { useState, useEffect, useMemo } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import TabButton from '@/components/tab-button'
import DifficultyBadge from '@/components/difficulty-badge'
import CodeBlock from '@/components/code-block'
import { ResizablePanel } from '../ui/resizable'
import { ImperativePanelHandle } from 'react-resizable-panels'
import {
  Discuss,
  PaginatedResponse,
  Problem,
  Solution,
  Status,
} from '@/lib/models'
import Script from 'next/script'
import { useAuth } from '@/components/auth-provider'
import useSWR from 'swr'
import { SubmissionSkeleton } from '@/components/loader'
import {
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Eye,
  MessageSquare,
  Star,
  Share2,
  Users,
} from 'lucide-react'
import Link from 'next/link'
import { apiFetcher, formatInUserTimezone } from '@/lib/utils'
import SubmissionResult from './submission-result'
import { AnimatePresence } from 'framer-motion'
import { apiFetch } from '@/lib/utils'
import EditorialTab from './editorial-tab'
import SolutionsTab from './solutions-tab'
import SolutionDetail from './solution-detail'
import { toast } from 'sonner'

declare global {
  interface Window {
    MathJax: any
  }
}

const tabs = [
  { id: 'description', label: 'Description', icon: 'description' },
  { id: 'editorial', label: 'Editorial', icon: 'edit_note' },
  { id: 'solutions', label: 'Solutions', icon: 'science' },
  { id: 'submissions', label: 'Submissions', icon: 'history' },
]

interface Props {
  problem: Problem
  maximizedSide?: 'left' | 'right' | null
  onMaximize?: () => void
  onRestore?: () => void
  ref?: React.Ref<ImperativePanelHandle>
  isContestMode?: boolean
  contestInfo?: {
    contest_id: number
    order?: number
    points?: number
    attempted_count?: number
    submitted_count?: number
    accepted_count?: number
  }
}

function ProblemDescription({
  problem,
  maximizedSide,
  onMaximize,
  onRestore,
  ref,
  isContestMode = false,
  contestInfo,
}: Props) {
  const searchParams = useSearchParams()
  const tabParam = searchParams?.get('tab')
  const submissionIdParam = searchParams?.get('submissionId')
  const discussionIdParam = searchParams?.get('discussionId')

  const [activeTab, setActiveTab] = useState(
    tabParam &&
      ['description', 'editorial', 'solutions', 'submissions'].includes(
        tabParam
      )
      ? tabParam
      : discussionIdParam
        ? 'solutions'
        : 'description'
  )
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<
    number | null
  >(null)
  const [selectedSubmission, setSelectedSubmission] = useState<Solution | null>(
    null
  )
  const [viewingSolution, setViewingSolution] = useState<Discuss | null>(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const { user } = useAuth()

  const { data: submissionsData } = useSWR<
    PaginatedResponse<Solution> | Solution[]
  >(user ? `solutions/?problem_id=${problem.id}` : null, apiFetcher)

  const { data: discussionsData } = useSWR<any>(
    !isContestMode ? `discussions/?problem_id=${problem.id}` : null,
    apiFetcher
  )

  const discussionsCount = useMemo(() => {
    if (Array.isArray(discussionsData)) return discussionsData.length
    if (typeof discussionsData?.count === 'number') return discussionsData.count
    if (Array.isArray(discussionsData?.results))
      return discussionsData.results.length
    return 0
  }, [discussionsData])

  const [likeCount, setLikeCount] = useState(problem.likes_count ?? 0)
  const [hasLiked, setHasLiked] = useState(!!problem.has_liked)
  const [dislikeCount, setDislikeCount] = useState(problem.dislikes_count ?? 0)
  const [hasDisliked, setHasDisliked] = useState(!!problem.has_disliked)
  const [viewsCount, setViewsCount] = useState(problem.views ?? 1)
  const [activeUsers, setActiveUsers] = useState(problem.active_users ?? 1)
  const [isStarred, setIsStarred] = useState(!!problem.is_favorited)
  const [isVoting, setIsVoting] = useState(false)

  // Sync state when problem props update
  useEffect(() => {
    if (problem) {
      if (typeof problem.likes_count === 'number')
        setLikeCount(problem.likes_count)
      if (typeof problem.has_liked === 'boolean') setHasLiked(problem.has_liked)
      if (typeof problem.dislikes_count === 'number')
        setDislikeCount(problem.dislikes_count)
      if (typeof problem.has_disliked === 'boolean')
        setHasDisliked(problem.has_disliked)
      if (typeof problem.views === 'number') setViewsCount(problem.views)
      if (typeof problem.active_users === 'number')
        setActiveUsers(problem.active_users)
      if (typeof problem.is_favorited === 'boolean')
        setIsStarred(problem.is_favorited)
    }
  }, [problem])

  // Periodic active users and views heartbeat
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await apiFetch(`problems/${problem.id}/heartbeat/`, {
          method: 'POST',
        })
        if (res.ok) {
          const data = await res.json()
          if (typeof data.active_users === 'number') {
            setActiveUsers(data.active_users)
          }
          if (typeof data.views === 'number') {
            setViewsCount(data.views)
          }
          if (typeof data.likes_count === 'number') {
            setLikeCount(data.likes_count)
          }
          if (typeof data.dislikes_count === 'number') {
            setDislikeCount(data.dislikes_count)
          }
        }
      } catch {
        // Silently ignore background heartbeat network errors
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [problem.id])

  const handleToggleLike = async () => {
    if (!user) {
      toast.error('Please sign in to vote on problems.')
      return
    }
    if (isVoting) return

    setIsVoting(true)
    // Optimistic state
    const prevLiked = hasLiked
    const prevDisliked = hasDisliked
    const prevLikeCount = likeCount
    const prevDislikeCount = dislikeCount

    if (hasLiked) {
      setHasLiked(false)
      setLikeCount((c) => Math.max(0, c - 1))
    } else {
      setHasLiked(true)
      setLikeCount((c) => c + 1)
      if (hasDisliked) {
        setHasDisliked(false)
        setDislikeCount((c) => Math.max(0, c - 1))
      }
    }

    try {
      const res = await apiFetch(`problems/${problem.id}/vote/`, {
        method: 'POST',
        body: JSON.stringify({ type: 'up' }),
      })
      if (res.ok) {
        const data = await res.json()
        setLikeCount(data.likes_count)
        setDislikeCount(data.dislikes_count)
        setHasLiked(data.has_liked)
        setHasDisliked(data.has_disliked)
      } else {
        throw new Error('Vote failed')
      }
    } catch {
      setHasLiked(prevLiked)
      setHasDisliked(prevDisliked)
      setLikeCount(prevLikeCount)
      setDislikeCount(prevDislikeCount)
      toast.error('Failed to update vote.')
    } finally {
      setIsVoting(false)
    }
  }

  const handleToggleDislike = async () => {
    if (!user) {
      toast.error('Please sign in to vote on problems.')
      return
    }
    if (isVoting) return

    setIsVoting(true)
    // Optimistic state
    const prevLiked = hasLiked
    const prevDisliked = hasDisliked
    const prevLikeCount = likeCount
    const prevDislikeCount = dislikeCount

    if (hasDisliked) {
      setHasDisliked(false)
      setDislikeCount((c) => Math.max(0, c - 1))
    } else {
      setHasDisliked(true)
      setDislikeCount((c) => c + 1)
      if (hasLiked) {
        setHasLiked(false)
        setLikeCount((c) => Math.max(0, c - 1))
      }
    }

    try {
      const res = await apiFetch(`problems/${problem.id}/vote/`, {
        method: 'POST',
        body: JSON.stringify({ type: 'down' }),
      })
      if (res.ok) {
        const data = await res.json()
        setLikeCount(data.likes_count)
        setDislikeCount(data.dislikes_count)
        setHasLiked(data.has_liked)
        setHasDisliked(data.has_disliked)
      } else {
        throw new Error('Vote failed')
      }
    } catch {
      setHasLiked(prevLiked)
      setHasDisliked(prevDisliked)
      setLikeCount(prevLikeCount)
      setDislikeCount(prevDislikeCount)
      toast.error('Failed to update vote.')
    } finally {
      setIsVoting(false)
    }
  }

  const handleToggleStar = async () => {
    if (!user) {
      toast.error('Please sign in to save problems to your favorites.')
      return
    }

    const prev = isStarred
    setIsStarred(!prev)
    toast.success(!prev ? 'Added to favorites list' : 'Removed from list')

    try {
      const res = await apiFetch(`problems/${problem.id}/favorite/`, {
        method: 'POST',
      })
      if (res.ok) {
        const data = await res.json()
        setIsStarred(data.is_favorited)
      } else {
        throw new Error('Favorite toggle failed')
      }
    } catch {
      setIsStarred(prev)
      toast.error('Failed to update favorites')
    }
  }

  const handleShare = () => {
    if (typeof window !== 'undefined') {
      navigator.clipboard.writeText(window.location.href)
      toast.success('Problem link copied to clipboard!')
    }
  }

  const history = useMemo(() => {
    const subs = Array.isArray(submissionsData)
      ? submissionsData
      : submissionsData?.results || []
    // Only include submissions that have results for graphing
    return subs.filter((s) => s.status === Status.SUCCESS && s.testcase_results)
  }, [submissionsData])

  useEffect(() => {
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise()
    }
  }, [problem, activeTab])

  const handleViewSubmission = async (id: number) => {
    setSelectedSubmissionId(id)
    setIsDetailLoading(true)
    try {
      const data = await apiFetch(`solutions/${id}/`)
      const json = await data.json()
      setSelectedSubmission(json)
    } catch (error) {
      console.error('Error fetching submission details:', error)
    } finally {
      setIsDetailLoading(false)
    }
  }

  const handleViewDiscussion = async (id: number) => {
    setIsDetailLoading(true)
    try {
      const data = await apiFetch(`discussions/${id}/`)
      if (data.ok) {
        const json = await data.json()
        setViewingSolution(json)
      }
    } catch (error) {
      console.error('Error fetching discussion details:', error)
    } finally {
      setIsDetailLoading(false)
    }
  }

  useEffect(() => {
    if (
      tabParam &&
      ['description', 'editorial', 'solutions', 'submissions'].includes(
        tabParam
      )
    ) {
      setActiveTab(tabParam)
    }
  }, [tabParam])

  useEffect(() => {
    if (submissionIdParam && !isNaN(Number(submissionIdParam))) {
      handleViewSubmission(Number(submissionIdParam))
    }
  }, [submissionIdParam])

  useEffect(() => {
    if (discussionIdParam && !isNaN(Number(discussionIdParam))) {
      setActiveTab('solutions')
      handleViewDiscussion(Number(discussionIdParam))
    }
  }, [discussionIdParam])

  const router = useRouter()
  const pathname = usePathname()

  const handleCloseSubmission = () => {
    setSelectedSubmission(null)
    setSelectedSubmissionId(null)
    setActiveTab('submissions')
    const params = new URLSearchParams(searchParams?.toString() || '')
    params.delete('submissionId')
    params.set('tab', 'submissions')
    const newQuery = params.toString() ? `?${params.toString()}` : ''
    router.replace(`${pathname}${newQuery}`, { scroll: false })
  }

  const handleCloseDiscussion = () => {
    setViewingSolution(null)
    setActiveTab('solutions')
    const params = new URLSearchParams(searchParams?.toString() || '')
    params.delete('discussionId')
    params.set('tab', 'solutions')
    const newQuery = params.toString() ? `?${params.toString()}` : ''
    router.replace(`${pathname}${newQuery}`, { scroll: false })
  }

  return (
    <ResizablePanel
      ref={ref}
      defaultSize={50}
      minSize={0}
      collapsible={true}
      className="flex flex-col border-r border-surface-border bg-background-dark overflow-hidden relative"
    >
      <AnimatePresence>
        {selectedSubmission && (
          <SubmissionResult
            solution={selectedSubmission}
            onClose={handleCloseSubmission}
            testcases={problem.testcases}
            history={history}
          />
        )}
        {viewingSolution && (
          <SolutionDetail
            solution={viewingSolution}
            onClose={handleCloseDiscussion}
            currentUser={user}
          />
        )}
      </AnimatePresence>

      {isDetailLoading && (
        <div className="absolute inset-0 bg-background-dark/50 z-[60] flex items-center justify-center">
          <div className="animate-spin size-8 border-4 border-primary border-t-transparent rounded-full"></div>
        </div>
      )}

      <Script id="mathjax-config" strategy="lazyOnload">
        {`
          window.MathJax = {
            tex: {
              inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
              displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
              processEscapes: true,
              processEnvironments: true
            },
            options: {
              skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }
          };
        `}
      </Script>
      <Script
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        strategy="lazyOnload"
      />
      {/* Tabs Header */}
      <div className="h-10 bg-surface-dark flex items-center px-2 gap-1 border-b border-surface-border shrink-0">
        {(isContestMode
          ? [
              { id: 'description', label: 'Description', icon: 'description' },
              { id: 'submissions', label: 'Submissions', icon: 'history' },
            ]
          : tabs
        ).map((tab) => (
          <TabButton
            key={tab.id}
            icon={tab.icon}
            label={tab.label}
            active={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          />
        ))}
        <div className="flex-1" />
        <div className="panel-right-btn flex space-x-1 pr-1">
          {maximizedSide === 'left' ? (
            <div data-state="closed">
              <button
                onClick={onRestore}
                title="Restore Panel"
                className="relative text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sd-ring disabled:pointer-events-none disabled:opacity-50 text-sd-foreground hover:text-sd-accent-foreground rounded-sd-md hover:bg-fill-secondary dark:hover:bg-fill-secondary flex h-6 w-6 cursor-pointer items-center justify-center !rounded p-[5px] fold text-gray-400 hover:text-white"
              >
                <div className="relative text-[14px] leading-[normal] p-[1px] before:block before:h-3.5 before:w-3.5 h-[14px] w-[14px] text-text-secondary dark:text-text-secondary">
                  <svg
                    aria-hidden="true"
                    focusable="false"
                    data-prefix="far"
                    data-icon="chevron-left"
                    className="svg-inline--fa fa-chevron-left absolute h-[1em] -translate-x-1/2 -translate-y-1/2 align-[-0.125em] left-1/2 top-1/2"
                    role="img"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 320 512"
                  >
                    <path
                      fill="currentColor"
                      d="M15 239c-9.4 9.4-9.4 24.6 0 33.9L207 465c9.4 9.4 24.6 9.4 33.9 0s9.4-24.6 0-33.9L65.9 256 241 81c9.4-9.4 9.4-24.6 0-33.9s-24.6-9.4-33.9 0L15 239z"
                    ></path>
                  </svg>
                </div>
              </button>
            </div>
          ) : (
            <div data-state="closed">
              <button
                onClick={onMaximize}
                title="Maximize Panel"
                className="relative text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sd-ring disabled:pointer-events-none disabled:opacity-50 text-sd-foreground hover:text-sd-accent-foreground rounded-sd-md hover:bg-fill-secondary dark:hover:bg-fill-secondary flex h-6 w-6 cursor-pointer items-center justify-center !rounded p-[5px] maximize text-gray-400 hover:text-white"
              >
                <div className="relative text-[14px] leading-[normal] p-[1px] before:block before:h-3.5 before:w-3.5 h-[14px] w-[14px] text-text-secondary dark:text-text-secondary">
                  <svg
                    aria-hidden="true"
                    focusable="false"
                    data-prefix="far"
                    data-icon="expand"
                    className="svg-inline--fa fa-expand absolute h-[1em] -translate-x-1/2 -translate-y-1/2 align-[-0.125em] left-1/2 top-1/2"
                    role="img"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 448 512"
                  >
                    <path
                      fill="currentColor"
                      d="M136 32c13.3 0 24 10.7 24 24s-10.7 24-24 24H48v88c0 13.3-10.7 24-24 24s-24-10.7-24-24V56C0 42.7 10.7 32 24 32H136zM0 344c0-13.3 10.7-24 24-24s24 10.7 24 24v88h88c13.3 0 24 10.7 24 24s-10.7 24-24 24H24c-13.3 0-24-10.7-24-24V344zM424 32c13.3 0 24 10.7 24 24V168c0 13.3-10.7 24-24 24s-24-10.7-24-24V80H312c-13.3 0-24-10.7-24-24s10.7-24 24-24H424zM400 344c0-13.3 10.7-24 24-24s24 10.7 24 24V456c0 13.3-10.7 24-24 24H312c-13.3 0-24-10.7-24-24s10.7-24 24-24h88V344z"
                    ></path>
                  </svg>
                </div>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Content Scroll Area */}
      <div className="flex-1 overflow-y-auto p-5 pb-10">
        {activeTab === 'description' && (
          <DescriptionContent
            problem={problem}
            isContestMode={isContestMode}
            contestInfo={contestInfo}
          />
        )}
        {!isContestMode && activeTab === 'editorial' && (
          <EditorialTab problem={problem} />
        )}
        {!isContestMode && activeTab === 'solutions' && (
          <SolutionsTab
            problem={problem}
            onViewSolution={(sol) => setViewingSolution(sol)}
          />
        )}
        {activeTab === 'submissions' && (
          <SubmissionsTab
            problemId={problem.id}
            authenticated={!!user}
            onViewDetail={handleViewSubmission}
          />
        )}
      </div>

      {/* Footer (Flex layout, scrollable content above is flex-1) */}
      <div className="w-full h-11 bg-surface-dark border-t border-surface-border flex items-center justify-between px-4 z-10 shrink-0 select-none">
        {isContestMode ? (
          <div className="text-gray-400 text-xs flex items-center gap-3">
            <span>
              Attempted:{' '}
              <b className="text-gray-200">
                {contestInfo?.attempted_count ?? 0}
              </b>
            </span>
            <span className="text-gray-600">|</span>
            <span>
              Submitted:{' '}
              <b className="text-gray-200">
                {contestInfo?.submitted_count ?? 0}
              </b>
            </span>
            <span className="text-gray-600">|</span>
            <span className="text-emerald-400">
              Accepted:{' '}
              <b className="text-emerald-300">
                {contestInfo?.accepted_count ?? 0}
              </b>
            </span>
          </div>
        ) : (
          <>
            {/* Left Actions: Like, Dislike, Views, Discussion */}
            <div className="flex items-center gap-3.5">
              <button
                onClick={handleToggleLike}
                className={`flex items-center gap-1 text-xs transition-colors ${
                  hasLiked
                    ? 'text-green-500 font-bold'
                    : 'text-gray-400 hover:text-green-500'
                }`}
                title="Like Problem"
              >
                <ThumbsUp className="size-3.5" />
                <span>{likeCount}</span>
              </button>

              <button
                onClick={handleToggleDislike}
                className={`flex items-center gap-1 text-xs transition-colors ${
                  hasDisliked
                    ? 'text-rose-500 font-bold'
                    : 'text-gray-400 hover:text-rose-500'
                }`}
                title="Dislike Problem"
              >
                <ThumbsDown className="size-3.5" />
                <span>{dislikeCount}</span>
              </button>

              <div
                className="flex items-center gap-1 text-xs text-gray-400"
                title="Total Views"
              >
                <Eye className="size-3.5 text-gray-500" />
                <span>{viewsCount.toLocaleString()}</span>
              </div>

              {/* Active Users Badge */}
              <div
                className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full"
                title={`${activeUsers} user${activeUsers === 1 ? '' : 's'} currently on this problem`}
              >
                <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <Users className="size-3 text-emerald-400" />
                <span className="font-semibold text-[11px]">
                  {activeUsers} online
                </span>
              </div>

              <div className="h-3.5 w-px bg-surface-border" />

              <button
                onClick={() => setActiveTab('solutions')}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
                title="View Discussions & Solutions"
              >
                <MessageSquare className="size-3.5" />
                <span>
                  Discussion{' '}
                  {discussionsCount > 0 ? `(${discussionsCount})` : ''}
                </span>
              </button>
            </div>

            {/* Right Actions: Star, Share */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleToggleStar}
                className={`flex items-center gap-1 text-xs transition-colors ${
                  isStarred
                    ? 'text-amber-400 font-bold'
                    : 'text-gray-400 hover:text-amber-400'
                }`}
                title="Add to List"
              >
                <Star
                  className={`size-3.5 ${isStarred ? 'fill-amber-400' : ''}`}
                />
                <span className="hidden sm:inline">Add to List</span>
              </button>

              <button
                onClick={handleShare}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-blue-400 transition-colors"
                title="Share Problem"
              >
                <Share2 className="size-3.5" />
                <span className="hidden sm:inline">Share</span>
              </button>
            </div>
          </>
        )}
      </div>
    </ResizablePanel>
  )
}

function DescriptionContent({
  problem,
  isContestMode,
  contestInfo,
}: {
  problem: Problem
  isContestMode?: boolean
  contestInfo?: {
    contest_id: number
    order?: number
    points?: number
    attempted_count?: number
    submitted_count?: number
    accepted_count?: number
  }
}) {
  const [showTags, setShowTags] = useState(false)

  return (
    <>
      {/* Title & Header */}
      <div className="flex justify-between items-start mb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight">
          {isContestMode && contestInfo?.order
            ? `Q${contestInfo.order}. ${problem.name}`
            : `${problem.id}. ${problem.name}`}
        </h1>
        <div className="flex gap-2">
          {!isContestMode && (
            <a
              href="#"
              className="text-gray-500 hover:text-white transition-colors"
            >
              <span className="material-symbols-outlined text-xl">help</span>
            </a>
          )}
        </div>
      </div>

      {/* Chips */}
      <div className="flex gap-2 mb-4 flex-wrap items-center">
        <DifficultyBadge difficulty={problem.difficulty ?? 'EASY'} />
        {isContestMode && contestInfo?.points && (
          <span className="bg-primary/20 text-primary border border-primary/30 text-xs font-bold px-2.5 py-0.5 rounded-full">
            {contestInfo.points} Points
          </span>
        )}
        {!isContestMode && (
          <>
            <div className="h-5 w-px bg-gray-700" />
            <button
              onClick={() => setShowTags(!showTags)}
              className="flex items-center gap-1 bg-surface-border hover:bg-muted px-2 py-0.5 rounded-full text-xs text-gray-300 transition-colors group"
            >
              <span className="material-symbols-outlined text-xs">sell</span>
              Topics
              <span
                className={`material-symbols-outlined text-sm transition-transform duration-200 ${
                  showTags ? 'rotate-180' : ''
                }`}
              >
                keyboard_arrow_down
              </span>
            </button>
          </>
        )}
      </div>

      {/* Tags List (Hidden during contest) */}
      {!isContestMode &&
        showTags &&
        problem.tags &&
        problem.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4 animate-in fade-in duration-200">
            {problem.tags.map((tag) => (
              <span
                key={tag.id}
                className="px-2 py-1 rounded bg-surface-border text-xs text-gray-400 font-medium hover:text-white transition-colors cursor-default"
              >
                {tag.tags}
              </span>
            ))}
          </div>
        )}

      {/* Problem Text */}
      <div className="text-sm text-gray-300 leading-relaxed space-y-4">
        <div
          dangerouslySetInnerHTML={{
            __html: problem?.problem_description ?? '',
          }}
        ></div>
      </div>
    </>
  )
}

function SubmissionsTab({
  problemId,
  authenticated,
  onViewDetail,
}: {
  problemId: number
  authenticated: boolean
  onViewDetail: (id: number) => void
}) {
  const { data, error, isLoading } = useSWR<
    PaginatedResponse<Solution> | Solution[]
  >(authenticated ? `solutions/?problem_id=${problemId}` : null, apiFetcher)

  if (!authenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
        <Clock size={48} className="text-gray-600" />
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-white">
            Sign in to view submissions
          </h3>
          <p className="text-gray-400 text-sm max-w-xs">
            You need to be logged in to track your progress and see your
            previous attempts.
          </p>
        </div>
        <Link href="/login">
          <button className="bg-primary hover:bg-primary/90 text-white px-6 py-2 rounded-lg font-bold transition-all">
            Sign In
          </button>
        </Link>
      </div>
    )
  }

  if (isLoading)
    return (
      <div className="py-4">
        <SubmissionSkeleton />
      </div>
    )

  if (error || !data)
    return (
      <div className="py-10 text-red-500 flex items-center gap-2">
        <AlertCircle size={20} />
        <span>Failed to load submissions</span>
      </div>
    )

  if (error || !data)
    return (
      <div className="py-10 text-red-500 flex items-center gap-2">
        <AlertCircle size={20} />
        <span>Failed to load submissions</span>
      </div>
    )

  const submissions: Solution[] = Array.isArray(data)
    ? data
    : data.results || []

  if (submissions.length === 0) {
    return (
      <div className="py-20 text-center space-y-4">
        <div className="text-gray-500 italic">No submissions yet</div>
        <p className="text-gray-600 text-sm">
          Submit your code to see your history here.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <h3 className="text-lg font-bold text-white mb-6">Past Submissions</h3>
      <div className="w-full overflow-x-auto rounded-xl border border-surface-border">
        <table className="w-full text-left border-collapse min-w-[400px]">
          <thead className="bg-surface-dark/50 text-gray-400 text-xs uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Language</th>
              <th className="px-4 py-3 font-medium">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border bg-background-dark">
            {submissions.map((sub) => (
              <tr
                key={sub.id}
                className="hover:bg-white/5 transition-colors group cursor-pointer"
                onClick={() => onViewDetail(sub.id)}
              >
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    {sub.status === Status.SUCCESS ? (
                      <CheckCircle2 size={16} className="text-green-500" />
                    ) : (
                      <XCircle size={16} className="text-red-500" />
                    )}
                    <span
                      className={`font-bold text-sm ${sub.status === Status.SUCCESS ? 'text-green-500' : 'text-red-500'}`}
                    >
                      {sub.status_display}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 text-sm text-gray-300">
                  {sub.language_display}
                </td>
                <td className="px-4 py-4 text-xs text-gray-500">
                  {formatInUserTimezone(sub.created_at, 'MMM d, yyyy HH:mm')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ProblemDescription
