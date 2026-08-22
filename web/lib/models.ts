// ============================================================================
// ENUMS
// ============================================================================

export enum Language {
  CPP = 'CPP',
  JAVA = 'JAVA',
  PYTHON = 'PYTHON',
  JAVASCRIPT = 'JAVASCRIPT',
  TYPESCRIPT = 'TYPESCRIPT',
}

// Judge0 Language IDs
export const LanguageCodes: Record<Language, number> = {
  [Language.CPP]: 54, // C++ (GCC 9.2.0)
  [Language.JAVA]: 62, // Java (OpenJDK 13.0.1)
  [Language.PYTHON]: 71, // Python (3.8.1)
  [Language.JAVASCRIPT]: 63, // JavaScript (Node.js 12.14.0)
  [Language.TYPESCRIPT]: 74, // TypeScript (3.7.4)
}

// Reverse mapping: Judge0 ID to Language enum
export const Judge0ToLanguage: Record<number, Language> = {
  54: Language.CPP,
  62: Language.JAVA,
  71: Language.PYTHON,
  63: Language.JAVASCRIPT,
  74: Language.TYPESCRIPT,
}

// Language display names
export const LanguageDisplayNames: Record<Language, string> = {
  [Language.CPP]: 'C++',
  [Language.JAVA]: 'Java',
  [Language.PYTHON]: 'Python',
  [Language.JAVASCRIPT]: 'JavaScript',
  [Language.TYPESCRIPT]: 'TypeScript',
}

export interface RunCodePayload {
  problem_id: number
  source_code: string
  language_id: number
  stdin?: string
  expected_output?: string

  number_of_runs?: number

  cpu_time_limit?: number
  cpu_extra_time?: number
  wall_time_limit?: number
  memory_limit?: number
  stack_limit?: number
  max_processes_and_or_threads?: number
  max_file_size?: number

  enable_per_process_and_thread_time_limit?: boolean
  enable_per_process_and_thread_memory_limit?: boolean
  enable_network?: boolean
}

export enum Difficulty {
  EASY = 'EASY',
  MEDIUM = 'MEDIUM',
  HARD = 'HARD',
}

export enum Status {
  QUEUE = 'In Queue',
  PROCESS = 'Processing',
  SUCCESS = 'Accepted',
  WRONG_ANSWER = 'Wrong Answer',
  TIME_LIMIT_EXCEEDED = 'Time Limit Exceeded',
  COMPILE_ERROR = 'Compilation Error',
  RUNTIME_ERROR_SIGSEGV = 'Runtime Error (SIGSEGV)',
  RUNTIME_ERROR_SIGXFSZ = 'Runtime Error (SIGXFSZ)',
  RUNTIME_ERROR_SIGFPE = 'Runtime Error (SIGFPE)',
  RUNTIME_ERROR_SIGABRT = 'Runtime Error (SIGABRT)',
  RUNTIME_ERROR_NZEC = 'Runtime Error (NZEC)',
  RUNTIME_ERROR_OTHER = 'Runtime Error (Other)',
  INTERNAL_ERROR = 'Internal Error',
  EXEC_FORMAT_ERROR = 'Exec Format Error',
  INVALID_TESTCASE = 'Invalid Testcase',
}

export enum DataType {
  STRING = 'string',
  INTEGER = 'integer',
}

// ============================================================================
// CORE MODEL INTERFACES
// ============================================================================

export interface User {
  id: number
  is_staff: boolean
  username: string
  email?: string
  name?: string | null
  default_lang?: Language
  profile_picture?: string | null
  profile_picture_url?: string | null
  date_joined: string
}

export interface UserRegistration {
  username: string
  email?: string
  name?: string | null
  password: string
  password2: string
  default_lang?: Language
}

export interface Tag {
  id: number
  tags: string
}

export interface Codeblock {
  id: number
  problem: number
  imports: string
  block: string
  runner_code: string
  language: Language
  language_display: string
  full_code: string
}

export interface Testcase {
  id: number
  problem: number
  input: string
  output: string
  display_testcase: boolean
  created_at: string
}

export interface TestcaseList {
  id: number
  input: string
  output: string
  display_testcase: boolean
  created_at: string
}

export interface Variable {
  id: number
  name: string
  type: string
  template_type?: string
  array_dimensions?: number
}

export interface Problem {
  id: number
  name: string
  problem_description?: string
  difficulty?: Difficulty
  tags: Tag[]
  codeblocks: Codeblock[]
  testcases: TestcaseList[]
  variables: Variable[]
  views?: number
  likes_count?: number
  dislikes_count?: number
  has_liked?: boolean
  has_disliked?: boolean
  is_favorited?: boolean
  active_users?: number
  created_at?: string
  is_multi?: boolean
  success_rate?: string
  total_solutions?: number
  total_testcases?: number
}

export interface ProblemList {
  id: number
  name: string
  problem_description?: string
  difficulty?: Difficulty
  tags: Tag[]
  created_at: string
  total_solutions: string
  total_testcases: string
}

export interface Solution {
  id: number
  user: User
  problem: number
  testcase_results: any
  code: string
  language: Language
  language_display: string
  status: Status | string | null
  status_display: string
  created_at: string
}

export interface SolutionList {
  id: number
  user: User
  problem_id: number
  language: Language
  language_display: string
  status: Status | string | null
  status_display: string
  created_at: string
}

export interface Discuss {
  id: number
  title: string
  body: string
  author: User
  problem: number
  tags: Tag[]
  views: number
  is_editorial: boolean
  upvote_count: number
  downvote_count: number
  comment_count: number
  has_upvoted?: boolean
  has_downvoted?: boolean
  comments?: Comment[]
  created_at: string
}

export interface Comment {
  id: number
  author: User
  discuss: number
  body: string
  parent: number | null
  replies: Comment[]
  upvote_count: number
  downvote_count: number
  has_upvoted?: boolean
  has_downvoted?: boolean
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AuthTokenRequest {
  username: string
  password: string
}

export interface AuthTokenResponse {
  token: string
}

export interface SolutionSubmitRequest {
  problem_id: number
  code: string
  language?: Language
}

export interface ProblemCreateRequest {
  name: string
  problem_description?: string
  difficulty?: Difficulty
  tag_ids?: number[]
}

export interface ProblemUpdateRequest {
  name?: string
  problem_description?: string
  difficulty?: Difficulty
  tag_ids?: number[]
}

export interface ProfileProblemSummary {
  id: number
  name: string
  difficulty: Difficulty
  last_submitted_at?: string
  created_at?: string
  tags?: string[]
}

export interface ProfileSubmission {
  id: number
  problem_id: number
  problem_name: string
  difficulty: Difficulty
  language: Language
  language_display: string
  status: Status | string | null
  status_display: string
  created_at: string
}

export interface HeatmapDay {
  date: string
  count: number
}

export interface ProfileStats {
  total_submissions: number
  successful_submissions: number
  unique_problems_attempted: number
  unique_problems_solved: number
  success_rate: number
  current_streak: number
  active_days: number
  difficulty_breakdown: Record<
    Difficulty,
    {
      solved: number
      attempted: number
    }
  >
  status_breakdown: Record<string, number>
}

export interface ProfileProblemDiscussion {
  id: number
  problem_id: number
  problem_name: string
  problem_difficulty: Difficulty
  title: string
  views: number
  upvotes_count: number
  downvotes_count: number
  is_editorial: boolean
  created_at: string
}

export interface ProfileGeneralDiscussion {
  id: number
  title: string
  category: string
  category_display: string
  views: number
  upvotes_count: number
  downvotes_count: number
  vote_count: number
  comments_count: number
  tags: string[]
  created_at: string
}

export interface UserProfile {
  user: User
  stats: ProfileStats
  heatmap: HeatmapDay[]
  recent_submissions: ProfileSubmission[]
  solved_problems: ProfileProblemSummary[]
  attempted_problems: ProfileProblemSummary[]
  favorite_problems?: ProfileProblemSummary[]
  problem_discussions?: ProfileProblemDiscussion[]
  general_discussions?: ProfileGeneralDiscussion[]
  available_years: number[]
  selected_year: number
}

// ============================================================================
// CONTEST INTERFACES
// ============================================================================

export type ContestStatus = 'UPCOMING' | 'ONGOING' | 'PAST'

export interface ContestProblemSummary {
  id: number
  problem_id: number
  order: number
  points: number
  name: string
  difficulty: Difficulty
  user_status: 'done' | 'attempted' | 'pending'
  attempted_count?: number
  submitted_count?: number
  accepted_count?: number
}

export interface Contest {
  id: number
  title: string
  slug: string
  description: string
  is_weekly: boolean
  start_time: string
  duration_minutes: number
  end_time: string
  status: ContestStatus
  is_published: boolean
  registered_count: number
  is_registered: boolean
  total_problems?: number
  problems?: ContestProblemSummary[]
  user_score?: number
  user_rank?: number | null
}

export interface ContestLeaderboardEntry {
  rank: number
  user_id: number
  username: string
  name: string | null
  profile_picture: string
  score: number
  penalty_seconds: number
  finish_time_seconds: number
  problems_solved: number
  problem_details: Record<
    string,
    {
      status: string
      wrong_attempts: number
      time_seconds: number
      points: number
    }
  >
  updated_at: string
}

export interface ContestLeaderboardResponse {
  contest_id: number
  contest_title: string
  contest_status: ContestStatus
  total_participants: number
  leaderboard: ContestLeaderboardEntry[]
  user_ranking?: ContestLeaderboardEntry | null
}

export interface ContestProblemDetail {
  id: number
  contest_id: number
  contest_title: string
  contest_status: ContestStatus
  contest_start_time: string
  contest_end_time: string
  problem_id: number
  order: number
  points: number
  name: string
  problem_description: string
  difficulty: Difficulty
  codeblocks: Codeblock[]
  testcases: TestcaseList[]
  variables: Variable[]
  user_status: 'done' | 'attempted' | 'pending'
  attempted_count: number
  submitted_count: number
  accepted_count: number
  prev_problem_id: number | null
  next_problem_id: number | null
  contest_problems: ContestProblemSummary[]
}

export type DiscussCategoryType =
  | 'ALL'
  | 'GENERAL'
  | 'INTERVIEW_EXPERIENCE'
  | 'INTERVIEW_QUESTION'
  | 'CAREER'
  | 'COMPENSATION'
  | 'FEEDBACK'

export interface DiscussCategoryItem {
  id: DiscussCategoryType
  label: string
  count: number
}

export interface DiscussAuthor {
  id: number
  username: string
  name: string
  profile_picture?: string | null
}

export interface DiscussComment {
  id: number
  post?: number
  author: DiscussAuthor
  parent: number | null
  content: string
  upvotes_count: number
  downvotes_count: number
  vote_count: number
  user_vote: 1 | -1 | 0
  replies: DiscussComment[]
  created_at: string
  updated_at: string
}

export interface DiscussPost {
  id: number
  author: DiscussAuthor
  title: string
  category: DiscussCategoryType
  category_display: string
  content_preview: string
  tags: string[]
  views: number
  vote_count: number
  comments_count: number
  pinned: boolean
  user_vote: 1 | -1 | 0
  created_at: string
  updated_at: string
}

export interface DiscussPostDetail extends DiscussPost {
  content: string
  comments: DiscussComment[]
}
