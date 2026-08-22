'use client'

import { useState } from 'react'
import Header from '@/components/header'
import PageTransition from '@/components/page-transition'
import useSWR from 'swr'
import { apiFetcher } from '@/lib/utils'
import {
  DiscussPost,
  DiscussCategoryItem,
  DiscussCategoryType,
  PaginatedResponse,
} from '@/lib/models'
import Link from 'next/link'
import {
  MessageSquare,
  Flame,
  Clock,
  TrendingUp,
  Eye,
  ThumbsUp,
  Search,
  Plus,
  Pin,
  Briefcase,
  HelpCircle,
  DollarSign,
  Compass,
  MessageCircleQuestion,
  Sparkles,
  ArrowRight,
  Filter,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useAuth } from '@/components/auth-provider'

const CATEGORY_ICONS: Record<string, any> = {
  ALL: Compass,
  GENERAL: MessageSquare,
  INTERVIEW_EXPERIENCE: Briefcase,
  INTERVIEW_QUESTION: MessageCircleQuestion,
  CAREER: TrendingUp,
  COMPENSATION: DollarSign,
  FEEDBACK: HelpCircle,
}

const CATEGORY_COLORS: Record<
  string,
  { bg: string; text: string; border: string }
> = {
  ALL: {
    bg: 'bg-primary/10',
    text: 'text-primary',
    border: 'border-primary/30',
  },
  GENERAL: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
  },
  INTERVIEW_EXPERIENCE: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
  },
  INTERVIEW_QUESTION: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
  },
  CAREER: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    border: 'border-purple-500/30',
  },
  COMPENSATION: {
    bg: 'bg-green-500/10',
    text: 'text-green-400',
    border: 'border-green-500/30',
  },
  FEEDBACK: {
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
  },
}

export default function DiscussHubPage() {
  const { user } = useAuth()
  const [selectedCategory, setSelectedCategory] =
    useState<DiscussCategoryType>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [order, setOrder] = useState<
    'hot' | 'newest' | 'most_voted' | 'most_viewed'
  >('hot')

  // Fetch categories with counts
  const { data: categories } = useSWR<DiscussCategoryItem[]>(
    'discuss/posts/categories/',
    apiFetcher
  )

  // Construct query string
  const query = new URLSearchParams({
    ...(selectedCategory !== 'ALL' && { category: selectedCategory }),
    ...(searchQuery && { search: searchQuery }),
    order: order,
  }).toString()

  const { data: postsData, isLoading } = useSWR<
    PaginatedResponse<DiscussPost> | DiscussPost[]
  >(`discuss/posts/?${query}`, apiFetcher)

  const posts = Array.isArray(postsData) ? postsData : postsData?.results || []

  // Top trending posts for sidebar
  const trendingPosts = [...posts]
    .sort((a, b) => b.views + b.vote_count * 2 - (a.views + a.vote_count * 2))
    .slice(0, 5)

  return (
    <PageTransition>
      <div className="min-h-screen bg-background-dark text-white flex flex-col font-sans">
        <Header />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 sm:px-6 lg:px-8">
          {/* Hero Banner / Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-surface-border">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="p-2 rounded-xl bg-primary/10 border border-primary/20 text-primary">
                  <MessageSquare className="size-5" />
                </span>
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                  Discussions & Community
                </h1>
              </div>
              <p className="text-gray-400 text-xs sm:text-sm max-w-2xl">
                Explore interview experiences, compensation talks, system design
                solutions, and connect with developers worldwide.
              </p>
            </div>

            <Link href="/discuss/new">
              <button className="bg-primary hover:bg-primary/90 text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-primary/20 transition-all hover:scale-105 active:scale-95">
                <Plus className="size-4" />
                <span>New Topic</span>
              </button>
            </Link>
          </div>

          {/* Category Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
            {(
              categories || [
                { id: 'ALL', label: 'All Topics', count: 0 },
                { id: 'GENERAL', label: 'General', count: 0 },
                {
                  id: 'INTERVIEW_EXPERIENCE',
                  label: 'Interview Exp',
                  count: 0,
                },
                { id: 'INTERVIEW_QUESTION', label: 'Questions', count: 0 },
                { id: 'CAREER', label: 'Career', count: 0 },
                { id: 'COMPENSATION', label: 'Compensation', count: 0 },
              ]
            ).map((cat) => {
              const Icon = CATEGORY_ICONS[cat.id] || MessageSquare
              const isSelected = selectedCategory === cat.id
              const colors = CATEGORY_COLORS[cat.id] || CATEGORY_COLORS.ALL

              return (
                <button
                  key={cat.id}
                  onClick={() =>
                    setSelectedCategory(cat.id as DiscussCategoryType)
                  }
                  className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'bg-surface-dark border-primary ring-1 ring-primary shadow-md'
                      : 'bg-surface-dark/50 border-surface-border hover:border-gray-600 hover:bg-surface-dark'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`p-1.5 rounded-lg ${colors.bg} ${colors.text}`}
                    >
                      <Icon className="size-4" />
                    </span>
                    <span className="text-[10px] font-mono text-gray-500 font-bold">
                      {cat.count}
                    </span>
                  </div>
                  <div>
                    <span className="font-bold text-xs text-gray-200 block truncate">
                      {cat.label}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Main Grid: Feed + Sidebar */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Feed Area (8 Cols) */}
            <div className="lg:col-span-8 space-y-4">
              {/* Search & Sort Controls Bar */}
              <div className="bg-surface-dark border border-surface-border rounded-xl p-3 flex flex-col sm:flex-row items-center justify-between gap-3">
                {/* Search Box */}
                <div className="relative w-full sm:w-72">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search topics, companies..."
                    className="w-full bg-background-dark border border-surface-border rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder:text-gray-500 focus:outline-none focus:border-primary"
                  />
                </div>

                {/* Sort Order Pills */}
                <div className="flex items-center gap-1 bg-background-dark p-1 rounded-lg border border-surface-border w-full sm:w-auto overflow-x-auto">
                  <button
                    onClick={() => setOrder('hot')}
                    className={`px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                      order === 'hot'
                        ? 'bg-primary text-white shadow-xs'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <Flame className="size-3" /> Hot
                  </button>
                  <button
                    onClick={() => setOrder('newest')}
                    className={`px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                      order === 'newest'
                        ? 'bg-primary text-white shadow-xs'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <Clock className="size-3" /> New
                  </button>
                  <button
                    onClick={() => setOrder('most_voted')}
                    className={`px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                      order === 'most_voted'
                        ? 'bg-primary text-white shadow-xs'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <ThumbsUp className="size-3" /> Top
                  </button>
                  <button
                    onClick={() => setOrder('most_viewed')}
                    className={`px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1.5 ${
                      order === 'most_viewed'
                        ? 'bg-primary text-white shadow-xs'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <Eye className="size-3" /> Most Viewed
                  </button>
                </div>
              </div>

              {/* Posts Feed List */}
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <div
                      key={n}
                      className="bg-surface-dark border border-surface-border rounded-xl p-5 animate-pulse space-y-3"
                    >
                      <div className="h-4 bg-gray-800 rounded w-1/4" />
                      <div className="h-5 bg-gray-700 rounded w-3/4" />
                      <div className="h-3 bg-gray-800 rounded w-full" />
                    </div>
                  ))}
                </div>
              ) : posts.length === 0 ? (
                <div className="bg-surface-dark border border-surface-border rounded-2xl p-12 text-center">
                  <MessageSquare className="size-12 text-gray-600 mx-auto mb-3" />
                  <h3 className="font-bold text-base text-gray-200">
                    No discussions found
                  </h3>
                  <p className="text-gray-500 text-xs mt-1 mb-4">
                    Be the first to start a conversation in this topic!
                  </p>
                  <Link href="/discuss/new">
                    <button className="bg-primary hover:bg-primary/90 text-white font-bold px-4 py-2 rounded-lg text-xs">
                      Create First Post
                    </button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {posts.map((post) => {
                    const colors =
                      CATEGORY_COLORS[post.category] || CATEGORY_COLORS.GENERAL

                    return (
                      <Link
                        key={post.id}
                        href={`/discuss/${post.id}`}
                        className="block bg-surface-dark border border-surface-border hover:border-gray-600 rounded-xl p-4 sm:p-5 transition-all hover:bg-surface-dark/80 group"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            {/* Category Badge & Pin */}
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              {post.pinned && (
                                <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                                  <Pin className="size-3" /> Pinned
                                </span>
                              )}
                              <span
                                className={`${colors.bg} ${colors.text} ${colors.border} border text-[10px] font-bold px-2.5 py-0.5 rounded-full`}
                              >
                                {post.category_display || post.category}
                              </span>
                            </div>

                            {/* Title */}
                            <h3 className="font-bold text-sm sm:text-base text-white group-hover:text-primary transition-colors line-clamp-1 mb-1.5">
                              {post.title}
                            </h3>

                            {/* Content Snippet */}
                            {post.content_preview && (
                              <p className="text-gray-400 text-xs line-clamp-2 leading-relaxed mb-3">
                                {post.content_preview}
                              </p>
                            )}

                            {/* Tags List */}
                            {post.tags && post.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 mb-3">
                                {post.tags.map((tag, idx) => (
                                  <span
                                    key={idx}
                                    className="bg-background-dark/80 text-gray-400 text-[10px] font-medium px-2 py-0.5 rounded-md border border-surface-border"
                                  >
                                    #{tag}
                                  </span>
                                ))}
                              </div>
                            )}

                            {/* Author & Timestamp */}
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Avatar className="size-5 border border-surface-border">
                                <AvatarImage
                                  src={post.author.profile_picture || undefined}
                                />
                                <AvatarFallback className="text-[10px]">
                                  {post.author.username
                                    .substring(0, 2)
                                    .toUpperCase()}
                                </AvatarFallback>
                              </Avatar>
                              <span className="text-gray-300 font-medium">
                                {post.author.name || post.author.username}
                              </span>
                              <span>·</span>
                              <span>
                                {new Date(post.created_at).toLocaleDateString(
                                  undefined,
                                  {
                                    month: 'short',
                                    day: 'numeric',
                                  }
                                )}
                              </span>
                            </div>
                          </div>

                          {/* Stats Counters (Right Side) */}
                          <div className="flex sm:flex-col items-end justify-center gap-2 sm:gap-1.5 shrink-0 text-right">
                            <div className="flex items-center gap-1 text-xs font-bold text-primary">
                              <ThumbsUp className="size-3.5" />
                              <span>{post.vote_count}</span>
                            </div>
                            <div className="flex items-center gap-1 text-xs text-gray-400">
                              <MessageSquare className="size-3.5" />
                              <span>{post.comments_count}</span>
                            </div>
                            <div className="flex items-center gap-1 text-[11px] text-gray-500 hidden sm:flex">
                              <Eye className="size-3" />
                              <span>{post.views}</span>
                            </div>
                          </div>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Right Sidebar (4 Cols) */}
            <div className="lg:col-span-4 space-y-6">
              {/* Start Topic Card */}
              <div className="bg-gradient-to-br from-primary/10 via-surface-dark to-surface-dark border border-primary/20 rounded-2xl p-5 shadow-lg">
                <div className="flex items-center gap-2 text-primary font-bold text-sm mb-2">
                  <Sparkles className="size-4" />
                  <span>Share Your Thoughts</span>
                </div>
                <p className="text-gray-300 text-xs leading-relaxed mb-4">
                  Got an interview experience to share, questions on
                  compensation, or career advice to ask? Post it to the
                  community!
                </p>
                <Link href="/discuss/new" className="block">
                  <button className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-2.5 rounded-xl text-xs flex items-center justify-center gap-2 shadow-md transition-all">
                    <Plus className="size-4" /> Create Discussion
                  </button>
                </Link>
              </div>

              {/* Trending Topics Widget */}
              <div className="bg-surface-dark border border-surface-border rounded-2xl p-5">
                <div className="flex items-center justify-between pb-3 border-b border-surface-border mb-4">
                  <div className="flex items-center gap-2">
                    <Flame className="size-4 text-amber-500" />
                    <h3 className="font-bold text-xs uppercase tracking-wider text-gray-300">
                      Trending Discussions
                    </h3>
                  </div>
                </div>

                <div className="space-y-3">
                  {trendingPosts.map((tp, idx) => (
                    <Link
                      key={tp.id}
                      href={`/discuss/${tp.id}`}
                      className="block group"
                    >
                      <div className="flex items-start gap-2.5">
                        <span className="text-xs font-bold text-gray-600 group-hover:text-primary mt-0.5">
                          #{idx + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-gray-200 group-hover:text-white line-clamp-2 transition-colors">
                            {tp.title}
                          </p>
                          <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500 font-mono">
                            <span>{tp.vote_count} votes</span>
                            <span>·</span>
                            <span>{tp.comments_count} replies</span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>

              {/* Community Guidelines */}
              <div className="bg-surface-dark/50 border border-surface-border rounded-2xl p-5">
                <h4 className="font-bold text-xs uppercase tracking-wider text-gray-400 mb-3">
                  Community Rules
                </h4>
                <ul className="space-y-2 text-xs text-gray-400 list-disc list-inside leading-relaxed">
                  <li>Be respectful and constructive in comments.</li>
                  <li>
                    Do not share confidential NDA interview questions directly.
                  </li>
                  <li>Use appropriate category tags for your topic.</li>
                  <li>Format code snippets using markdown blocks.</li>
                </ul>
              </div>
            </div>
          </div>
        </main>
      </div>
    </PageTransition>
  )
}
