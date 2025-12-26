// ============================================================================
// ENUMS
// ============================================================================

export enum Language {
  CPP = 'CPP',
  JAVA = 'JAVA',
  PYTHON = 'PYTHON',
  JAVASCRIPT = 'JAVASCRIPT',
  TYPESCRIPT = 'TYPESCRIPT'
}

// Judge0 Language IDs
export const LanguageCodes: Record<Language, number> = {
  [Language.CPP]: 54,        // C++ (GCC 9.2.0)
  [Language.JAVA]: 62,       // Java (OpenJDK 13.0.1)
  [Language.PYTHON]: 71,     // Python (3.8.1)
  [Language.JAVASCRIPT]: 63, // JavaScript (Node.js 12.14.0)
  [Language.TYPESCRIPT]: 74  // TypeScript (3.7.4)
};

// Reverse mapping: Judge0 ID to Language enum
export const Judge0ToLanguage: Record<number, Language> = {
  54: Language.CPP,
  62: Language.JAVA,
  71: Language.PYTHON,
  63: Language.JAVASCRIPT,
  74: Language.TYPESCRIPT
};

// Language display names
export const LanguageDisplayNames: Record<Language, string> = {
  [Language.CPP]: 'C++',
  [Language.JAVA]: 'Java',
  [Language.PYTHON]: 'Python',
  [Language.JAVASCRIPT]: 'JavaScript',
  [Language.TYPESCRIPT]: 'TypeScript'
};

export enum Difficulty {
  EASY = 'EASY',
  MEDIUM = 'MEDIUM',
  HARD = 'HARD'
}

export enum Status {
  INVALID_TESTCASE = 'INVALID_TESTCASE',
  RUNTIME_ERROR = 'RUNTIME_ERROR',
  COMPILE_ERROR = 'COMPILE_ERROR',
  WRONG_ANSWER = 'WRONG_ANSWER',
  SUCCESS = 'SUCCESS',
  TIME_LIMIT_EXCEEDED = 'TIME_LIMIT_EXCEEDED',
  MEMORY_LIMIT_EXCEEDED = 'MEMORY_LIMIT_EXCEEDED'
}

// ============================================================================
// CORE MODEL INTERFACES
// ============================================================================

export interface User {
  id: number;
  username: string;
  email?: string;
  name?: string | null;
  default_lang?: Language;
  date_joined: string;
}

export interface UserRegistration {
  username: string;
  email?: string;
  name?: string | null;
  password: string;
  password2: string;
  default_lang?: Language;
}

export interface Tag {
  id: number;
  tags: string;
}

export interface Codeblock {
  id: number;
  problem: number;
  block: string;
  language: Language;
  language_display: string;
}

export interface Testcase {
  id: number;
  problem: number;
  input: string;
  output: string;
  created_at: string;
}

export interface TestcaseList {
  id: number;
  input: string;
  output: string;
  created_at: string;
}

export interface Problem {
  id: number;
  name: string;
  problem_description?: string;
  difficulty?: Difficulty;
  tags: Tag[];
  codeblocks: Codeblock[];
  testcases: TestcaseList[];
  created_at: string;
  success_rate: string;
}

export interface ProblemList {
  id: number;
  name: string;
  problem_description?: string;
  difficulty?: Difficulty;
  tags: Tag[];
  created_at: string;
  total_solutions: string;
  total_testcases: string;
}

export interface Solution {
  id: number;
  user: User;
  problem: number;
  code: string;
  language: Language;
  language_display: string;
  status: Status | null;
  status_display: string;
  created_at: string;
}

export interface SolutionList {
  id: number;
  user: User;
  problem_id: number;
  language: Language;
  language_display: string;
  status: Status | null;
  status_display: string;
  created_at: string;
}

export interface Discussion {
  id: number;
  title: string;
  body?: string;
  author: User;
  user: User;
  problem: number;
  tags: Tag[];
  created_at: string;
}

export interface DiscussionList {
  id: number;
  title: string;
  author: User;
  problem_id: number;
  tags: Tag[];
  created_at: string;
}

// ============================================================================
// REQUEST/RESPONSE TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AuthTokenRequest {
  username: string;
  password: string;
}

export interface AuthTokenResponse {
  token: string;
}

export interface SolutionSubmitRequest {
  problem_id: number;
  code: string;
  language?: Language;
}

export interface ProblemCreateRequest {
  name: string;
  problem_description?: string;
  difficulty?: Difficulty;
  tag_ids?: number[];
}

export interface ProblemUpdateRequest {
  name?: string;
  problem_description?: string;
  difficulty?: Difficulty;
  tag_ids?: number[];
}

export interface DiscussionCreateRequest {
  title: string;
  body?: string;
  problem: number;
  tag_ids?: number[];
}

export interface DiscussionUpdateRequest {
  title?: string;
  body?: string;
  problem?: number;
  tag_ids?: number[];
}

export interface CodeblockCreateRequest {
  problem: number;
  block: string;
  language: Language;
}

export interface TestcaseCreateRequest {
  problem: number;
  input: string;
  output: string;
}

export interface UserUpdateRequest {
  username?: string;
  email?: string;
  name?: string | null;
  default_lang?: Language;
}

// ============================================================================
// API SERVICE INTERFACES
// ============================================================================

export interface IAuthService {
  login(data: AuthTokenRequest): Promise<AuthTokenResponse>;
  logout(): Promise<void>;
  register(data: UserRegistration): Promise<void>;
  getCurrentUser(): Promise<User>;
  updateProfile(data: UserUpdateRequest): Promise<User>;
  changePassword(oldPassword: string, newPassword: string): Promise<User>;
  getUserStats(): Promise<any>;
}

export interface IProblemService {
  list(params?: {
    ordering?: string;
    page?: number;
    search?: string;
  }): Promise<PaginatedResponse<ProblemList>>;
  get(id: number): Promise<Problem>;
  create(data: ProblemCreateRequest): Promise<Problem>;
  update(id: number, data: ProblemUpdateRequest): Promise<Problem>;
  partialUpdate(id: number, data: Partial<ProblemUpdateRequest>): Promise<Problem>;
  delete(id: number): Promise<void>;
  getByTag(tag: string): Promise<Problem[]>;
  getMyAttempts(): Promise<Problem[]>;
  getDiscussions(id: number): Promise<Discussion[]>;
  getSolutions(id: number): Promise<Solution[]>;
  getStatistics(id: number): Promise<any>;
}

export interface ISolutionService {
  list(params?: {
    ordering?: string;
    page?: number;
  }): Promise<PaginatedResponse<SolutionList>>;
  get(id: number): Promise<Solution>;
  create(data: SolutionSubmitRequest): Promise<Solution>;
  update(id: number, data: Partial<Solution>): Promise<Solution>;
  partialUpdate(id: number, data: Partial<Solution>): Promise<Solution>;
  delete(id: number): Promise<void>;
  submit(data: SolutionSubmitRequest): Promise<any>;
  getMySolutions(): Promise<Solution[]>;
  getStatistics(): Promise<any>;
}

export interface IDiscussionService {
  list(params?: {
    ordering?: string;
    page?: number;
    search?: string;
  }): Promise<PaginatedResponse<DiscussionList>>;
  get(id: number): Promise<Discussion>;
  create(data: DiscussionCreateRequest): Promise<Discussion>;
  update(id: number, data: DiscussionUpdateRequest): Promise<Discussion>;
  partialUpdate(id: number, data: Partial<DiscussionUpdateRequest>): Promise<Discussion>;
  delete(id: number): Promise<void>;
  getByProblem(problemId: number): Promise<Discussion[]>;
  getMyDiscussions(): Promise<Discussion[]>;
}

export interface ICodeblockService {
  list(params?: {
    ordering?: string;
    page?: number;
    search?: string;
  }): Promise<PaginatedResponse<Codeblock>>;
  get(id: number): Promise<Codeblock>;
  create(data: CodeblockCreateRequest): Promise<Codeblock>;
  update(id: number, data: CodeblockCreateRequest): Promise<Codeblock>;
  partialUpdate(id: number, data: Partial<CodeblockCreateRequest>): Promise<Codeblock>;
  delete(id: number): Promise<void>;
}

export interface ITestcaseService {
  list(params?: {
    ordering?: string;
    page?: number;
    search?: string;
  }): Promise<PaginatedResponse<Testcase>>;
  get(id: number): Promise<Testcase>;
  create(data: TestcaseCreateRequest): Promise<Testcase>;
  update(id: number, data: TestcaseCreateRequest): Promise<Testcase>;
  partialUpdate(id: number, data: Partial<TestcaseCreateRequest>): Promise<Testcase>;
  delete(id: number): Promise<void>;
}

export interface ITagService {
  list(params?: {
    page?: number;
    search?: string;
  }): Promise<PaginatedResponse<Tag>>;
  get(id: number): Promise<Tag>;
  create(data: { tags: string }): Promise<Tag>;
  update(id: number, data: { tags: string }): Promise<Tag>;
  partialUpdate(id: number, data: Partial<{ tags: string }>): Promise<Tag>;
  delete(id: number): Promise<void>;
  getPopular(): Promise<Tag[]>;
  getProblems(id: number): Promise<Problem[]>;
}

export interface IUserService {
  list(params?: {
    ordering?: string;
    page?: number;
    search?: string;
  }): Promise<PaginatedResponse<User>>;
  get(id: number): Promise<User>;
  update(id: number, data: UserUpdateRequest): Promise<User>;
  partialUpdate(id: number, data: Partial<UserUpdateRequest>): Promise<User>;
  delete(id: number): Promise<void>;
}

// ============================================================================
// API CLIENT CONFIGURATION
// ============================================================================

export interface ApiConfig {
  baseUrl: string;
  token?: string;
  headers?: Record<string, string>;
}

export interface ApiClient {
  auth: IAuthService;
  problems: IProblemService;
  solutions: ISolutionService;
  discussions: IDiscussionService;
  codeblocks: ICodeblockService;
  testcases: ITestcaseService;
  tags: ITagService;
  users: IUserService;
}