'use client'

import { useState, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Header from '@/components/header'
import PageTransition from '@/components/page-transition'
import useSWR from 'swr'
import { apiFetcher, apiFetch } from '@/lib/utils'
import { DiscussPostDetail, DiscussComment } from '@/lib/models'
import Link from 'next/link'
import {
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Eye,
  Share2,
  ChevronLeft,
  Pin,
  Send,
  Trash2,
  Reply,
  Sparkles,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useAuth } from '@/components/auth-provider'
import { toast } from 'sonner'

export default function DiscussDetailPage() {
  const params = useParams()
  const postId = params.id as string
  const router = useRouter()
  const { user } = useAuth()

  const [commentText, setCommentText] = useState('')
  const [replyingToId, setReplyingToId] = useState<number | null>(null)
  const [replyText, setReplyText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    data: post,
    error,
    isLoading,
    mutate,
  } = useSWR<DiscussPostDetail>(`discuss/posts/${postId}/`, apiFetcher)

  const totalCommentsCount = useMemo(() => {
    if (!post) return 0
    if (typeof post.comments_count === 'number' && post.comments_count > 0) {
      return post.comments_count
    }
    if (!post.comments) return 0
    const countTree = (list: DiscussComment[]): number => {
      return list.reduce(
        (acc, c) => acc + 1 + (c.replies ? countTree(c.replies) : 0),
        0
      )
    }
    return countTree(post.comments)
  }, [post])

  // Vote on post handler
  const handleVote = async (voteType: 'up' | 'down') => {
    if (!user) {
      toast.error('Please sign in to vote.')
      return
    }

    try {
      const res = await apiFetch(`discuss/posts/${postId}/vote/`, {
        method: 'POST',
        body: JSON.stringify({ vote_type: voteType }),
      })
      if (res.ok) {
        const data = await res.json()
        mutate(
          (prev) =>
            prev
              ? {
                  ...prev,
                  vote_count: data.vote_count,
                  user_vote: data.user_vote,
                }
              : prev,
          false
        )
      }
    } catch (err) {
      console.error('Failed to vote on post:', err)
    }
  }

  // Add top-level comment handler
  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) {
      toast.error('Please sign in to comment.')
      return
    }
    if (!commentText.trim()) return

    setIsSubmitting(true)
    try {
      const res = await apiFetch(`discuss/posts/${postId}/add_comment/`, {
        method: 'POST',
        body: JSON.stringify({ content: commentText.trim() }),
      })
      if (res.ok) {
        setCommentText('')
        toast.success('Comment posted!')
        mutate()
      } else {
        const errData = await res.json()
        toast.error(errData.error || 'Failed to post comment.')
      }
    } catch (err) {
      toast.error('Network error posting comment.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Add reply to comment handler
  const handleAddReply = async (parentId: number) => {
    if (!user) {
      toast.error('Please sign in to reply.')
      return
    }
    if (!replyText.trim()) return

    setIsSubmitting(true)
    try {
      const res = await apiFetch(`discuss/posts/${postId}/add_comment/`, {
        method: 'POST',
        body: JSON.stringify({
          content: replyText.trim(),
          parent_id: parentId,
        }),
      })
      if (res.ok) {
        setReplyText('')
        setReplyingToId(null)
        toast.success('Reply posted!')
        mutate()
      }
    } catch (err) {
      toast.error('Failed to post reply.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Vote (up/down) comment handler
  const handleCommentVote = async (commentId: number, type: 'up' | 'down') => {
    if (!user) {
      toast.error('Please sign in to vote on comments.')
      return
    }

    try {
      const res = await apiFetch(`discuss/comments/${commentId}/vote/`, {
        method: 'POST',
        body: JSON.stringify({ type }),
      })
      if (res.ok) {
        mutate()
      }
    } catch (err) {
      console.error('Failed to vote on comment:', err)
      toast.error('Failed to update comment vote.')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background-dark text-white flex flex-col">
        <Header />
        <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 space-y-4">
          <div className="h-6 bg-surface-dark rounded w-1/4 animate-pulse" />
          <div className="h-10 bg-surface-dark rounded w-3/4 animate-pulse" />
          <div className="h-48 bg-surface-dark rounded-xl animate-pulse" />
        </main>
      </div>
    )
  }

  if (error || !post) {
    return (
      <div className="min-h-screen bg-background-dark text-white flex flex-col">
        <Header />
        <div className="flex-1 flex flex-col items-center justify-center p-4">
          <h2 className="text-xl font-bold mb-2">Discussion Not Found</h2>
          <p className="text-gray-400 text-xs mb-4">
            This discussion may have been removed or does not exist.
          </p>
          <Link href="/discuss">
            <button className="bg-primary px-4 py-2 rounded-lg text-xs font-bold">
              Back to Discussions
            </button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-background-dark text-white flex flex-col font-sans">
        <Header />

        <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 sm:px-6">
          {/* Back button */}
          <Link
            href="/discuss"
            className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white mb-6 transition-colors group"
          >
            <ChevronLeft className="size-4 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back to All Discussions</span>
          </Link>

          {/* Main Post Card */}
          <article className="bg-surface-dark border border-surface-border rounded-2xl p-6 sm:p-8 mb-8 shadow-xl">
            {/* Header info */}
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                <Avatar className="size-10 border border-surface-border">
                  <AvatarImage src={post.author.profile_picture || undefined} />
                  <AvatarFallback className="text-xs font-bold">
                    {post.author.username.substring(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h4 className="font-bold text-sm text-white">
                    {post.author.name || post.author.username}
                  </h4>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>
                      {new Date(post.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                    <span>·</span>
                    <span className="flex items-center gap-1">
                      <Eye className="size-3" /> {post.views} views
                    </span>
                  </div>
                </div>
              </div>

              {/* Category Badge */}
              <div className="flex items-center gap-2">
                {post.pinned && (
                  <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                    <Pin className="size-3" /> Pinned
                  </span>
                )}
                <span className="bg-primary/20 text-primary border border-primary/30 text-xs font-bold px-3 py-1 rounded-full">
                  {post.category_display || post.category}
                </span>
              </div>
            </div>

            {/* Title */}
            <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight mb-6">
              {post.title}
            </h1>

            {/* Content Body */}
            <div className="text-sm text-gray-300 leading-relaxed space-y-4 whitespace-pre-wrap font-normal mb-8 border-b border-surface-border pb-8">
              {post.content}
            </div>

            {/* Tags */}
            {post.tags && post.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {post.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="bg-background-dark text-gray-300 text-xs font-medium px-2.5 py-1 rounded-lg border border-surface-border"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {/* Footer Actions: Upvote / Downvote & Share */}
            <div className="flex items-center justify-between pt-4">
              <div className="flex items-center gap-2 bg-background-dark p-1 rounded-xl border border-surface-border">
                <button
                  onClick={() => handleVote('up')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
                    post.user_vote === 1
                      ? 'bg-primary text-white shadow-xs'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <ThumbsUp className="size-3.5" />
                  <span>Upvote ({post.vote_count})</span>
                </button>
                <div className="h-4 w-px bg-surface-border" />
                <button
                  onClick={() => handleVote('down')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
                    post.user_vote === -1
                      ? 'bg-rose-500 text-white shadow-xs'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <ThumbsDown className="size-3.5" />
                </button>
              </div>

              <button
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href)
                  toast.success('Link copied to clipboard!')
                }}
                className="text-gray-400 hover:text-white text-xs font-medium flex items-center gap-1.5 bg-background-dark px-3 py-2 rounded-xl border border-surface-border hover:border-gray-600 transition-colors"
              >
                <Share2 className="size-3.5" />
                <span>Share</span>
              </button>
            </div>
          </article>

          {/* Comments Section */}
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-lg text-white flex items-center gap-2">
                <MessageSquare className="size-5 text-primary" />
                <span>Comments ({totalCommentsCount})</span>
              </h3>
            </div>

            {/* Add Comment Input */}
            <form
              onSubmit={handleAddComment}
              className="bg-surface-dark border border-surface-border rounded-2xl p-4 space-y-3"
            >
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder={
                  user
                    ? 'Write a comment or share your insights...'
                    : 'Sign in to join the conversation...'
                }
                disabled={!user || isSubmitting}
                rows={3}
                className="w-full bg-background-dark border border-surface-border rounded-xl p-3 text-xs text-white placeholder:text-gray-500 focus:outline-none focus:border-primary resize-none disabled:opacity-60"
              />
              <div className="flex justify-between items-center">
                <span className="text-[11px] text-gray-500">
                  Markdown supported
                </span>
                <button
                  type="submit"
                  disabled={!user || !commentText.trim() || isSubmitting}
                  className="bg-primary hover:bg-primary/90 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-md"
                >
                  <Send className="size-3.5" />
                  <span>Post Comment</span>
                </button>
              </div>
            </form>

            {/* Comments List */}
            <div className="space-y-4">
              {post.comments && post.comments.length > 0 ? (
                post.comments.map((comment) => (
                  <div
                    key={comment.id}
                    className="bg-surface-dark border border-surface-border rounded-2xl p-5 space-y-3"
                  >
                    {/* Comment Author Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <Avatar className="size-7 border border-surface-border">
                          <AvatarImage
                            src={comment.author.profile_picture || undefined}
                          />
                          <AvatarFallback className="text-[10px] font-bold">
                            {comment.author.username
                              .substring(0, 2)
                              .toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <span className="font-bold text-xs text-white">
                            {comment.author.name || comment.author.username}
                          </span>
                          <span className="text-[11px] text-gray-500 ml-2">
                            {new Date(comment.created_at).toLocaleDateString(
                              undefined,
                              { month: 'short', day: 'numeric' }
                            )}
                          </span>
                        </div>
                      </div>

                      {/* Comment Upvote & Downvote */}
                      <div className="flex items-center gap-1 bg-background-dark/80 rounded-lg border border-surface-border p-0.5">
                        <button
                          onClick={() => handleCommentVote(comment.id, 'up')}
                          className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-md transition-colors ${
                            comment.user_vote === 1
                              ? 'text-primary bg-primary/10'
                              : 'text-gray-400 hover:text-white'
                          }`}
                          title="Upvote comment"
                        >
                          <ThumbsUp className="size-3" />
                          <span>{comment.upvotes_count ?? 0}</span>
                        </button>
                        <div className="w-px h-3 bg-surface-border" />
                        <button
                          onClick={() => handleCommentVote(comment.id, 'down')}
                          className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-md transition-colors ${
                            comment.user_vote === -1
                              ? 'text-rose-500 bg-rose-500/10'
                              : 'text-gray-400 hover:text-white'
                          }`}
                          title="Downvote comment"
                        >
                          <ThumbsDown className="size-3" />
                          <span>{comment.downvotes_count ?? 0}</span>
                        </button>
                      </div>
                    </div>

                    {/* Comment Content */}
                    <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap pl-9">
                      {comment.content}
                    </p>

                    {/* Reply Action */}
                    <div className="pl-9 pt-1">
                      <button
                        onClick={() =>
                          setReplyingToId(
                            replyingToId === comment.id ? null : comment.id
                          )
                        }
                        className="text-[11px] text-gray-400 hover:text-primary flex items-center gap-1 font-medium transition-colors"
                      >
                        <Reply className="size-3" /> Reply
                      </button>

                      {/* Reply Box */}
                      {replyingToId === comment.id && (
                        <div className="mt-3 space-y-2">
                          <textarea
                            value={replyText}
                            onChange={(e) => setReplyText(e.target.value)}
                            placeholder={`Reply to ${comment.author.username}...`}
                            rows={2}
                            className="w-full bg-background-dark border border-surface-border rounded-xl p-2.5 text-xs text-white placeholder:text-gray-500 focus:outline-none focus:border-primary resize-none"
                          />
                          <div className="flex gap-2 justify-end">
                            <button
                              onClick={() => setReplyingToId(null)}
                              className="text-xs text-gray-400 hover:text-white px-3 py-1"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => handleAddReply(comment.id)}
                              disabled={!replyText.trim() || isSubmitting}
                              className="bg-primary hover:bg-primary/90 text-white font-bold px-3 py-1 rounded-lg text-xs disabled:opacity-50"
                            >
                              Send Reply
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Nested Replies */}
                    {comment.replies && comment.replies.length > 0 && (
                      <div className="pl-9 pt-2 space-y-3 border-l-2 border-surface-border ml-3 mt-2">
                        {comment.replies.map((reply) => (
                          <div
                            key={reply.id}
                            className="bg-background-dark/60 p-3 rounded-xl border border-surface-border"
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <div className="flex items-center gap-2">
                                <Avatar className="size-5 border border-surface-border">
                                  <AvatarImage
                                    src={
                                      reply.author.profile_picture || undefined
                                    }
                                  />
                                  <AvatarFallback className="text-[9px]">
                                    {reply.author.username
                                      .substring(0, 2)
                                      .toUpperCase()}
                                  </AvatarFallback>
                                </Avatar>
                                <span className="font-bold text-[11px] text-gray-300">
                                  {reply.author.name || reply.author.username}
                                </span>
                              </div>
                              <div className="flex items-center gap-1 bg-surface-dark/80 rounded px-1 py-0.5 border border-surface-border/50">
                                <button
                                  onClick={() =>
                                    handleCommentVote(reply.id, 'up')
                                  }
                                  className={`text-[10px] flex items-center gap-1 transition-colors ${
                                    reply.user_vote === 1
                                      ? 'text-primary font-bold'
                                      : 'text-gray-400 hover:text-white'
                                  }`}
                                  title="Upvote reply"
                                >
                                  <ThumbsUp className="size-2.5" />
                                  <span>{reply.upvotes_count ?? 0}</span>
                                </button>
                                <div className="w-px h-2.5 bg-surface-border" />
                                <button
                                  onClick={() =>
                                    handleCommentVote(reply.id, 'down')
                                  }
                                  className={`text-[10px] flex items-center gap-1 transition-colors ${
                                    reply.user_vote === -1
                                      ? 'text-rose-500 font-bold'
                                      : 'text-gray-400 hover:text-white'
                                  }`}
                                  title="Downvote reply"
                                >
                                  <ThumbsDown className="size-2.5" />
                                  <span>{reply.downvotes_count ?? 0}</span>
                                </button>
                              </div>
                            </div>
                            <p className="text-xs text-gray-300 whitespace-pre-wrap">
                              {reply.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="bg-surface-dark/50 border border-surface-border rounded-xl p-8 text-center text-xs text-gray-500">
                  No comments yet. Be the first to share your thoughts!
                </div>
              )}
            </div>
          </section>
        </main>
      </div>
    </PageTransition>
  )
}
