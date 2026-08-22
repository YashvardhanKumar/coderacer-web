'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Header from '@/components/header'
import PageTransition from '@/components/page-transition'
import { apiFetch } from '@/lib/utils'
import { DiscussCategoryType } from '@/lib/models'
import Link from 'next/link'
import {
  ChevronLeft,
  Sparkles,
  Send,
  HelpCircle,
  Eye,
  Edit3,
} from 'lucide-react'
import { useAuth } from '@/components/auth-provider'
import { toast } from 'sonner'

const CATEGORIES: { id: DiscussCategoryType; label: string; desc: string }[] = [
  {
    id: 'GENERAL',
    label: 'General Discussion',
    desc: 'General software engineering, tech talks, algorithms, and discussions.',
  },
  {
    id: 'INTERVIEW_EXPERIENCE',
    label: 'Interview Experience',
    desc: 'Share your onsite, OA, and technical interview journeys and outcomes.',
  },
  {
    id: 'INTERVIEW_QUESTION',
    label: 'Interview Question',
    desc: 'Discuss real coding and system design questions asked in interviews.',
  },
  {
    id: 'CAREER',
    label: 'Career & Growth',
    desc: 'Resume reviews, career transitions, promotion guidance, and advice.',
  },
  {
    id: 'COMPENSATION',
    label: 'Compensation & Offers',
    desc: 'Salary data, offer evaluations, negotiations, and leveling benchmarks.',
  },
  {
    id: 'FEEDBACK',
    label: 'Feedback & Suggestions',
    desc: 'Platform feature requests, ideas, and improvement suggestions.',
  },
]

export default function NewDiscussPostPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  const [category, setCategory] = useState<DiscussCategoryType>('GENERAL')
  const [title, setTitle] = useState('')
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [content, setContent] = useState('')
  const [activeTab, setActiveTab] = useState<'write' | 'preview'>('write')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Handle adding tag
  const handleAddTag = () => {
    const trimmed = tagInput.trim().replace(/^#/, '')
    if (trimmed && !tags.includes(trimmed) && tags.length < 5) {
      setTags([...tags, trimmed])
      setTagInput('')
    }
  }

  // Handle remove tag
  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) {
      toast.error('Please sign in to publish a discussion.')
      router.push('/login')
      return
    }

    if (!title.trim() || title.length < 5) {
      toast.error('Title must be at least 5 characters long.')
      return
    }

    if (!content.trim() || content.length < 20) {
      toast.error('Content must be at least 20 characters long.')
      return
    }

    setIsSubmitting(true)
    try {
      const res = await apiFetch('discuss/posts/', {
        method: 'POST',
        body: JSON.stringify({
          category,
          title: title.trim(),
          content: content.trim(),
          tags,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        toast.success('Discussion topic created successfully!')
        router.push(`/discuss/${data.id}`)
      } else {
        const errData = await res.json()
        toast.error(
          errData.detail || errData.title?.[0] || 'Failed to create discussion.'
        )
      }
    } catch (err) {
      toast.error('Network error creating topic.')
    } finally {
      setIsSubmitting(false)
    }
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
            <span>Back to Discussions</span>
          </Link>

          <div className="bg-surface-dark border border-surface-border rounded-2xl p-6 sm:p-8 shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between pb-6 border-b border-surface-border mb-6">
              <div>
                <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
                  <Sparkles className="size-5 text-primary" />
                  <span>Create Discussion Topic</span>
                </h1>
                <p className="text-gray-400 text-xs mt-1">
                  Share insights, interview experiences, questions, or
                  compensation details with the community.
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Category Selector */}
              <div>
                <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                  Category <span className="text-rose-400">*</span>
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {CATEGORIES.map((cat) => (
                    <div
                      key={cat.id}
                      onClick={() => setCategory(cat.id)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        category === cat.id
                          ? 'bg-primary/10 border-primary ring-1 ring-primary'
                          : 'bg-background-dark/70 border-surface-border hover:border-gray-600'
                      }`}
                    >
                      <span className="font-bold text-xs text-white block">
                        {cat.label}
                      </span>
                      <span className="text-[11px] text-gray-400 block mt-0.5 line-clamp-1">
                        {cat.desc}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Title Input */}
              <div>
                <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                  Title <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Google L5 System Design Interview Experience (Dec 2025)"
                  className="w-full bg-background-dark border border-surface-border rounded-xl p-3 text-xs sm:text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-primary"
                  required
                />
              </div>

              {/* Tags Input */}
              <div>
                <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
                  Tags{' '}
                  <span className="text-gray-500 font-normal">
                    (Optional, max 5)
                  </span>
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddTag()
                      }
                    }}
                    placeholder="e.g. Google, System Design, L5"
                    className="flex-1 bg-background-dark border border-surface-border rounded-xl px-3 py-2 text-xs text-white placeholder:text-gray-500 focus:outline-none focus:border-primary"
                  />
                  <button
                    type="button"
                    onClick={handleAddTag}
                    className="bg-surface-border hover:bg-muted text-gray-200 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                  >
                    Add Tag
                  </button>
                </div>
                {tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {tags.map((tag) => (
                      <span
                        key={tag}
                        className="bg-primary/10 border border-primary/30 text-primary text-xs font-medium px-2.5 py-0.5 rounded-md flex items-center gap-1"
                      >
                        #{tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="hover:text-rose-400 ml-1 font-bold"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Content Editor & Preview */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider">
                    Content Body <span className="text-rose-400">*</span>
                  </label>
                  <div className="flex gap-1 bg-background-dark p-0.5 rounded-lg border border-surface-border">
                    <button
                      type="button"
                      onClick={() => setActiveTab('write')}
                      className={`px-2.5 py-1 rounded text-xs font-bold flex items-center gap-1 ${
                        activeTab === 'write'
                          ? 'bg-primary text-white'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      <Edit3 className="size-3" /> Write
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab('preview')}
                      className={`px-2.5 py-1 rounded text-xs font-bold flex items-center gap-1 ${
                        activeTab === 'preview'
                          ? 'bg-primary text-white'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      <Eye className="size-3" /> Preview
                    </button>
                  </div>
                </div>

                {activeTab === 'write' ? (
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Write your discussion content here. Markdown formatting and code blocks are supported..."
                    rows={12}
                    className="w-full bg-background-dark border border-surface-border rounded-xl p-3.5 text-xs sm:text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-primary resize-y font-mono"
                    required
                  />
                ) : (
                  <div className="min-h-[280px] bg-background-dark border border-surface-border rounded-xl p-4 text-xs sm:text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {content || (
                      <span className="text-gray-600 italic">
                        Nothing to preview yet. Write some content first.
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Submit Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-surface-border">
                <Link href="/discuss">
                  <button
                    type="button"
                    className="text-gray-400 hover:text-white text-xs font-bold px-4 py-2"
                  >
                    Cancel
                  </button>
                </Link>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-primary hover:bg-primary/90 text-white font-bold px-6 py-2.5 rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-primary/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
                >
                  <Send className="size-4" />
                  <span>
                    {isSubmitting ? 'Publishing...' : 'Publish Discussion'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </main>
      </div>
    </PageTransition>
  )
}
