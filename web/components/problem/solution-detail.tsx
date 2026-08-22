'use client'
import { useState, useEffect, useMemo } from 'react'
import { Discuss, Comment, User } from '@/lib/models'
import { apiFetch, formatInUserTimezone } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeRaw from 'rehype-raw'
import rehypeKatex from 'rehype-katex'
import Link from 'next/link'
import CodeBlock from '../code-block'
import {
  X,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Share2,
  MoreVertical,
  User as UserIcon,
  Reply,
  Send,
  Loader2,
  Eye,
} from 'lucide-react'
import { Button } from '../ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar'
import { Badge } from '../ui/badge'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { Input } from '../ui/input'

interface Props {
  solution: Discuss
  onClose: () => void
  currentUser: User | null
}

export default function SolutionDetail({
  solution: initialSolution,
  onClose,
  currentUser,
}: Props) {
  const [solution, setSolution] = useState<Discuss>(initialSolution)
  const [comments, setComments] = useState<Comment[]>([])
  const [isVoting, setIsVoting] = useState(false)
  const [newComment, setNewComment] = useState('')
  const [isSubmittingComment, setIsSubmittingComment] = useState(false)
  const [replyingTo, setReplyingTo] = useState<number | null>(null)

  const totalCommentsCount = useMemo(() => {
    const countTree = (list: Comment[]): number => {
      return list.reduce(
        (acc, c) => acc + 1 + (c.replies ? countTree(c.replies) : 0),
        0
      )
    }
    const treeCount = countTree(comments)
    if (treeCount > 0) return treeCount
    if (typeof solution.comment_count === 'number')
      return solution.comment_count
    return 0
  }, [comments, solution.comment_count])

  useEffect(() => {
    // Fetch fresh detail with comments and views incremented
    async function fetchDetail() {
      try {
        const response = await apiFetch(`discussions/${initialSolution.id}/`)
        const data = await response.json()
        setSolution(data)
        if (data.comments) setComments(data.comments)
      } catch (err) {
        console.error('Error fetching solution detail:', err)
      }
    }
    fetchDetail()
  }, [initialSolution.id])

  const handleVote = async (type: 'up' | 'down') => {
    if (!currentUser) {
      toast.error('Please sign in to vote')
      return
    }
    setIsVoting(true)
    try {
      const response = await apiFetch(
        `discussions/${solution.id}/${type}vote/`,
        {
          method: 'POST',
        }
      )
      if (response.ok) {
        const data = await response.json()
        setSolution((prev) => ({
          ...prev,
          upvote_count: data.upvote_count ?? prev.upvote_count,
          downvote_count: data.downvote_count ?? prev.downvote_count,
          has_upvoted: data.has_upvoted ?? false,
          has_downvoted: data.has_downvoted ?? false,
        }))
      }
    } catch (err) {
      toast.error('Failed to vote')
    } finally {
      setIsVoting(false)
    }
  }

  const handleSubmitComment = async (parentId: number | null = null) => {
    if (!currentUser) {
      toast.error('Please sign in to comment')
      return
    }
    const body = parentId
      ? (document.getElementById(`reply-input-${parentId}`) as HTMLInputElement)
          ?.value
      : newComment
    if (!body?.trim()) return

    setIsSubmittingComment(true)
    try {
      const response = await apiFetch(
        `discussions/${solution.id}/add_comment/`,
        {
          method: 'POST',
          body: JSON.stringify({ body, parent_id: parentId }),
        }
      )
      if (response.ok) {
        const commentData = await response.json()
        if (parentId) {
          // Find parent and add to its replies
          setComments((prev) =>
            prev.map((c) => {
              if (c.id === parentId) {
                return { ...c, replies: [...(c.replies || []), commentData] }
              }
              return c
            })
          )
          setReplyingTo(null)
        } else {
          setComments((prev) => [commentData, ...prev])
          setNewComment('')
        }
        toast.success('Comment added')
      }
    } catch (err) {
      toast.error('Failed to add comment')
    } finally {
      setIsSubmittingComment(false)
    }
  }

  const handleVoteComment = async (commentId: number, type: 'up' | 'down') => {
    if (!currentUser) {
      toast.error('Please sign in to vote on comments')
      return
    }

    const updateTree = (list: Comment[]): Comment[] => {
      return list.map((c) => {
        if (c.id === commentId) {
          const wasUp = !!c.has_upvoted
          const wasDown = !!c.has_downvoted
          let upCount = c.upvote_count ?? 0
          let downCount = c.downvote_count ?? 0
          let newUp = wasUp
          let newDown = wasDown

          if (type === 'up') {
            if (wasUp) {
              newUp = false
              upCount = Math.max(0, upCount - 1)
            } else {
              newUp = true
              upCount += 1
              if (wasDown) {
                newDown = false
                downCount = Math.max(0, downCount - 1)
              }
            }
          } else {
            if (wasDown) {
              newDown = false
              downCount = Math.max(0, downCount - 1)
            } else {
              newDown = true
              downCount += 1
              if (wasUp) {
                newUp = false
                upCount = Math.max(0, upCount - 1)
              }
            }
          }

          return {
            ...c,
            upvote_count: upCount,
            downvote_count: downCount,
            has_upvoted: newUp,
            has_downvoted: newDown,
          }
        }
        if (c.replies && c.replies.length > 0) {
          return { ...c, replies: updateTree(c.replies) }
        }
        return c
      })
    }

    setComments((prev) => updateTree(prev))

    try {
      const response = await apiFetch(
        `discussions/comment/${commentId}/vote/`,
        {
          method: 'POST',
          body: JSON.stringify({ type }),
        }
      )
      if (response.ok) {
        const data = await response.json()
        const syncTree = (list: Comment[]): Comment[] => {
          return list.map((c) => {
            if (c.id === commentId) {
              return {
                ...c,
                upvote_count: data.upvote_count,
                downvote_count: data.downvote_count,
                has_upvoted: data.has_upvoted,
                has_downvoted: data.has_downvoted,
              }
            }
            if (c.replies && c.replies.length > 0) {
              return { ...c, replies: syncTree(c.replies) }
            }
            return c
          })
        }
        setComments((prev) => syncTree(prev))
      }
    } catch {
      toast.error('Failed to vote on comment')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="absolute inset-0 bg-background-dark z-50 flex flex-col overflow-hidden"
    >
      {/* Header */}
      <div className="h-12 border-b border-surface-border flex items-center justify-between px-6 bg-surface-dark/50 shrink-0">
        <div className="flex items-center gap-3">
          <Badge
            variant="secondary"
            className="bg-primary/20 text-primary border-none text-[10px] uppercase font-bold tracking-wider"
          >
            Solution
          </Badge>
          <h2 className="text-sm font-bold text-white truncate max-w-[200px] md:max-w-md">
            {solution.title}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors p-1"
        >
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6 space-y-8 pb-32">
          {/* Author Header */}
          <div className="flex items-start justify-between">
            <div className="flex gap-4">
              <Avatar className="size-12 rounded-xl border border-surface-border">
                <AvatarImage
                  src={
                    solution.author?.profile_picture_url ||
                    (solution.author as any)?.profile_picture ||
                    (solution as any).user?.profile_picture_url ||
                    (solution as any).user?.profile_picture ||
                    undefined
                  }
                />
                <AvatarFallback className="bg-surface-border text-gray-400">
                  <UserIcon size={24} />
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-bold text-white">
                  {solution.author?.name ||
                    solution.author?.username ||
                    (solution as any).user?.name ||
                    (solution as any).user?.username ||
                    'Anonymous'}
                </h3>
                <p className="text-xs text-gray-500">
                  Posted on{' '}
                  {solution.created_at
                    ? formatInUserTimezone(solution.created_at, 'MMMM d, yyyy')
                    : 'recently'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-gray-500"
              >
                <Share2 size={16} />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-gray-500"
              >
                <MoreVertical size={16} />
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="prose prose-invert max-w-none prose-sm prose-headings:text-white prose-p:text-gray-300 prose-code:before:content-none prose-code:after:content-none bg-surface-dark/30 p-6 rounded-2xl border border-surface-border">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeRaw, rehypeKatex]}
              components={{
                pre: ({ children }) => <>{children}</>,

                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '')
                  return !inline && match ? (
                    <CodeBlock
                      code={String(children).replace(/\n$/, '')}
                      language={match[1]}
                    />
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                },
                p: ({ children }) => {
                  const content = Array.isArray(children)
                    ? children
                    : [children]
                  return (
                    <p>
                      {content.map((child, i) => {
                        if (typeof child === 'string' && child.includes('@')) {
                          return child.split(/(@\w+)/).map((part, j) =>
                            part.startsWith('@') ? (
                              <Link
                                key={j}
                                href={`/profile/${part.slice(1)}`}
                                className="text-primary hover:underline"
                              >
                                {part}
                              </Link>
                            ) : (
                              part
                            )
                          )
                        }
                        return child
                      })}
                    </p>
                  )
                },
              }}
            >
              {solution.body}
            </ReactMarkdown>
          </div>

          {/* Voting & Stats */}
          <div className="flex items-center gap-6 border-t border-b border-surface-border py-4">
            <div className="flex items-center gap-1 bg-surface-dark rounded-lg border border-surface-border p-1">
              <Button
                variant="ghost"
                size="sm"
                className={`h-8 gap-2 ${solution.has_upvoted ? 'text-primary bg-primary/10' : 'text-gray-500'}`}
                onClick={() => handleVote('up')}
                disabled={isVoting}
              >
                <ThumbsUp size={16} />
                <span className="text-xs font-bold">
                  {solution.upvote_count}
                </span>
              </Button>
              <div className="w-px h-4 bg-surface-border" />
              <Button
                variant="ghost"
                size="sm"
                className={`h-8 gap-2 ${solution.has_downvoted ? 'text-red-500 bg-red-500/10' : 'text-gray-500'}`}
                onClick={() => handleVote('down')}
                disabled={isVoting}
              >
                <ThumbsDown size={16} />
                <span className="text-xs font-bold">
                  {solution.downvote_count}
                </span>
              </Button>
            </div>
            <div className="flex items-center gap-2 text-gray-500 text-xs font-medium">
              <Eye size={16} />
              <span>{solution.views} Views</span>
            </div>
          </div>

          {/* Comments Section */}
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <MessageSquare size={20} className="text-primary" />
              Comments ({totalCommentsCount})
            </h3>

            {/* Main Comment Input */}
            <div className="flex gap-4">
              <Avatar className="size-8 rounded-lg border border-surface-border shrink-0">
                <AvatarImage
                  src={currentUser?.profile_picture_url ?? undefined}
                />
                <AvatarFallback className="bg-surface-border text-gray-400">
                  <UserIcon size={16} />
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 space-y-2">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Type comment here... (Markdown supported)"
                  className="w-full bg-surface-dark border border-surface-border rounded-xl p-3 text-sm text-gray-300 focus:outline-none focus:border-primary min-h-[80px] resize-none"
                />
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    className="gap-2 bg-primary hover:bg-primary/90"
                    onClick={() => handleSubmitComment()}
                    disabled={isSubmittingComment || !newComment.trim()}
                  >
                    {isSubmittingComment ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Send size={14} />
                    )}
                    Post Comment
                  </Button>
                </div>
              </div>
            </div>

            {/* Comments List */}
            <div className="space-y-6 pt-4">
              {comments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onReply={() => setReplyingTo(comment.id)}
                  isReplying={replyingTo === comment.id}
                  onCancelReply={() => setReplyingTo(null)}
                  onSubmitReply={() => handleSubmitComment(comment.id)}
                  isSubmitting={isSubmittingComment}
                  onVote={(type) => handleVoteComment(comment.id, type)}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function CommentItem({
  comment,
  onReply,
  isReplying,
  onCancelReply,
  onSubmitReply,
  isSubmitting,
  onVote,
}: {
  comment: Comment
  onReply: () => void
  isReplying: boolean
  onCancelReply: () => void
  onSubmitReply: () => void
  isSubmitting: boolean
  onVote: (type: 'up' | 'down') => void
}) {
  return (
    <div className="group space-y-4">
      <div className="flex gap-4">
        <Avatar className="size-8 rounded-lg border border-surface-border shrink-0">
          <AvatarImage
            src={
              comment.author?.profile_picture_url ||
              (comment.author as any)?.profile_picture ||
              undefined
            }
          />
          <AvatarFallback className="bg-surface-border text-gray-400">
            <UserIcon size={16} />
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-white">
              {comment.author?.name ||
                comment.author?.username ||
                (comment as any).user?.username ||
                'Anonymous'}
            </span>
            <span className="text-[10px] text-gray-600">
              {comment.created_at
                ? formatInUserTimezone(comment.created_at, 'MMM d, yyyy')
                : ''}
            </span>
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">
            {comment.body}
          </p>
          <div className="flex items-center gap-4 pt-1">
            <button
              className="text-[10px] font-bold text-gray-500 hover:text-primary transition-colors flex items-center gap-1"
              onClick={onReply}
            >
              <Reply size={12} /> Reply
            </button>
            <div className="flex items-center gap-3">
              <button
                onClick={() => onVote('up')}
                className={`text-[10px] font-bold transition-colors flex items-center gap-1 ${
                  comment.has_upvoted
                    ? 'text-primary'
                    : 'text-gray-500 hover:text-primary'
                }`}
                title="Upvote comment"
              >
                <ThumbsUp size={12} /> {comment.upvote_count ?? 0}
              </button>
              <button
                onClick={() => onVote('down')}
                className={`text-[10px] font-bold transition-colors flex items-center gap-1 ${
                  comment.has_downvoted
                    ? 'text-red-500'
                    : 'text-gray-500 hover:text-red-500'
                }`}
                title="Downvote comment"
              >
                <ThumbsDown size={12} /> {comment.downvote_count ?? 0}
              </button>
            </div>
          </div>

          {/* Reply Input */}
          <AnimatePresence>
            {isReplying && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden pt-3"
              >
                <div className="flex flex-col gap-2">
                  <textarea
                    id={`reply-input-${comment.id}`}
                    placeholder={`Reply to @${
                      comment.author?.username || 'user'
                    }...`}
                    className="w-full bg-surface-dark border border-surface-border rounded-lg p-2 text-xs text-gray-300 focus:outline-none focus:border-primary min-h-[60px] resize-none"
                    defaultValue={
                      comment.author?.username
                        ? `@${comment.author.username} `
                        : ''
                    }
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-[10px]"
                      onClick={onCancelReply}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      className="h-7 text-[10px] bg-primary hover:bg-primary/90"
                      onClick={onSubmitReply}
                      disabled={isSubmitting}
                    >
                      {isSubmitting && (
                        <Loader2 size={10} className="animate-spin mr-1" />
                      )}
                      Post Reply
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Nested Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="pl-12 space-y-4 border-l border-surface-border/50">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              onReply={onReply}
              isReplying={false}
              onCancelReply={() => {}}
              onSubmitReply={() => {}}
              isSubmitting={false}
              onVote={onVote}
            />
          ))}
        </div>
      )}
    </div>
  )
}
