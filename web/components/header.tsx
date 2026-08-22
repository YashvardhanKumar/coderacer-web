'use client'

import Link from 'next/link'
import Logo from '@/components/logo'
import { useAuth } from './auth-provider'
import { Button } from './ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Skeleton } from './ui/skeleton'
import IconButton from '@/components/icon-button'
import { cn } from '@/lib/utils'

import { usePathname } from 'next/navigation'

interface HeaderProps {
  variant?: 'default' | 'problem'
}

export function UserMenu() {
  const { user, loading, logout } = useAuth()

  if (loading) {
    return <Skeleton className="size-8 rounded-full" />
  }

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link href="/login">
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-700 dark:text-white hover:bg-slate-100 dark:hover:bg-surface-border"
          >
            Sign In
          </Button>
        </Link>
        <Link href="/signup">
          <Button
            size="sm"
            className="bg-primary hover:bg-primary/90 text-white"
          >
            Sign Up
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div className="flex items-center gap-2 cursor-pointer group">
          <Avatar className="size-8 border border-slate-200 dark:border-surface-border transition-transform group-hover:scale-110">
            <AvatarImage
              src={
                user.profile_picture_url ||
                `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.username}`
              }
            />
            <AvatarFallback>
              {user.username.substring(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-56 border-slate-200 dark:border-surface-border bg-white dark:bg-background-dark"
      >
        <DropdownMenuLabel>
          <div className="flex flex-col">
            <span className="font-bold text-slate-900 dark:text-white">
              {user.name || user.username}
            </span>
            <span className="text-xs text-slate-500 dark:text-text-secondary">
              {user.email}
            </span>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-slate-200 dark:bg-surface-border" />
        <DropdownMenuItem
          asChild
          className="cursor-pointer hover:bg-slate-100 dark:hover:bg-surface-border"
        >
          <Link href="/profile">
            <span className="material-symbols-outlined mr-2 text-lg">
              person
            </span>
            Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem className="cursor-pointer hover:bg-slate-100 dark:hover:bg-surface-border">
          <span className="material-symbols-outlined mr-2 text-lg">
            settings
          </span>
          Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-slate-200 dark:bg-surface-border" />
        <DropdownMenuItem
          className="cursor-pointer text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30"
          onClick={logout}
        >
          <span className="material-symbols-outlined mr-2 text-lg">logout</span>
          Logout
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default function Header({ variant = 'default' }: HeaderProps) {
  const isProblem = variant === 'problem'
  const pathname = usePathname()

  const isProblemsActive = pathname?.startsWith('/problems')
  const isContestActive = pathname?.startsWith('/contest')
  const isDiscussActive = pathname?.startsWith('/discuss')
  const isStoreActive = pathname?.startsWith('/store')

  return (
    <header
      className={cn(
        'sticky top-0 z-50 flex items-center justify-between whitespace-nowrap border-b border-solid transition-colors',
        isProblem
          ? 'h-12.5 border-b-surface-border bg-surface-dark px-4'
          : 'px-6 py-3 border-slate-200 dark:border-surface-border bg-white dark:bg-background-dark shadow-sm dark:shadow-none'
      )}
    >
      <div className="flex items-center gap-3 md:gap-8">
        <Logo variant={isProblem ? 'problem' : 'default'} />

        {isProblem ? (
          <>
            <div className="h-4 w-px bg-gray-600 hidden md:block" />
            <nav className="flex items-center gap-4">
              <Link
                href="/problems"
                className="flex items-center gap-1 text-gray-300 hover:text-white text-sm font-medium"
              >
                <span className="material-symbols-outlined text-lg">list</span>
                Problem List
              </Link>
              <div className="hidden sm:flex items-center gap-1 text-gray-400 text-sm">
                <IconButton icon="chevron_left" title="Previous Problem" />
                <IconButton icon="chevron_right" title="Next Problem" />
                <IconButton icon="shuffle" title="Random Problem" />
              </div>
            </nav>
          </>
        ) : (
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/problems"
              className={cn(
                'text-sm font-medium leading-normal py-4 -my-4 transition-all',
                isProblemsActive
                  ? 'text-slate-900 dark:text-white border-b-2 border-primary'
                  : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white hover:-translate-y-0.5'
              )}
            >
              Problems
            </Link>
            <Link
              href="/contest"
              className={cn(
                'text-sm font-medium leading-normal py-4 -my-4 transition-all',
                isContestActive
                  ? 'text-slate-900 dark:text-white border-b-2 border-primary'
                  : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white hover:-translate-y-0.5'
              )}
            >
              Contest
            </Link>
            <Link
              href="/discuss"
              className={cn(
                'text-sm font-medium leading-normal py-4 -my-4 transition-all',
                isDiscussActive
                  ? 'text-slate-900 dark:text-white border-b-2 border-primary'
                  : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white hover:-translate-y-0.5'
              )}
            >
              Discuss
            </Link>
            <Link
              href="/store"
              className={cn(
                'text-primary text-sm font-medium leading-normal flex items-center gap-1 transition-all hover:scale-110 active:scale-95 py-4 -my-4',
                isStoreActive && 'border-b-2 border-primary'
              )}
            >
              Store
            </Link>
          </nav>
        )}
      </div>

      <div className="flex flex-1 justify-end gap-4 md:gap-8 items-center">
        {!isProblem && (
          <label className="hidden md:flex flex-col min-w-40 h-9! max-w-64 group">
            <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-slate-100 dark:bg-surface-border overflow-hidden transition-all group-focus-within:ring-2 group-focus-within:ring-primary/50 group-focus-within:bg-white dark:group-focus-within:bg-slate-800">
              <div className="text-slate-400 dark:text-text-secondary flex items-center justify-center pl-3 group-focus-within:text-primary transition-colors">
                <span className="material-symbols-outlined text-xl">
                  search
                </span>
              </div>
              <input
                className="flex w-full min-w-0 flex-1 resize-none bg-transparent border-none text-slate-900 dark:text-white focus:outline-0 focus:ring-0 placeholder:text-slate-400 dark:placeholder:text-text-secondary px-3 text-sm font-normal leading-normal"
                placeholder="Search"
              />
            </div>
          </label>
        )}

        <div className="flex items-center gap-4">
          {isProblem && (
            <button className="hidden md:flex bg-surface-border hover:bg-muted text-gray-300 px-3 py-1.5 rounded text-xs font-medium items-center gap-2 transition-colors">
              <span className="material-symbols-outlined text-base text-yellow-500">
                bug_report
              </span>
              Debug
            </button>
          )}

          <button
            className={cn(
              'hidden sm:flex items-center justify-center overflow-hidden rounded-lg h-9 px-4 text-xs font-bold uppercase tracking-wider transition-all active:scale-95',
              isProblem
                ? 'bg-primary/20 hover:bg-primary/30 text-primary'
                : 'bg-primary/10 hover:bg-primary/20 text-primary hover:shadow-lg hover:shadow-primary/10'
            )}
          >
            Premium
          </button>

          <div className="flex items-center gap-4">
            <button
              className={cn(
                'relative hover:scale-110 transition-transform',
                isProblem
                  ? 'text-gray-400 hover:text-white'
                  : 'text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white'
              )}
            >
              <span className="material-symbols-outlined text-xl">
                notifications
              </span>
              {isProblem && (
                <span className="absolute top-0 right-0 size-2 bg-red-500 rounded-full" />
              )}
            </button>

            <UserMenu />
          </div>
        </div>
      </div>
    </header>
  )
}
