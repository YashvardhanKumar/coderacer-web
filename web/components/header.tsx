// import Link from 'next/link';

// export default function Header() {
//   return (
//     <header className="sticky top-0 z-50 flex items-center justify-between whitespace-nowrap border-b border-solid border-slate-200 dark:border-surface-border bg-white dark:bg-[#181b23] px-6 py-3 shadow-sm dark:shadow-none">
//       <div className="flex items-center gap-8">
//         <Link href="/" className="flex items-center gap-2 text-slate-900 dark:text-white cursor-pointer">
//           <div className="size-8 text-primary">
//             <svg fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
//               <path d="M13.483 0a1.374 1.374 0 0 0-.961.438L7.129 5.836H2.628a2.63 2.63 0 0 0-2.628 2.628v8.623a2.63 2.63 0 0 0 2.628 2.628h1.867l-1.04 3.733A1.4 1.4 0 0 0 4.8 25.13l.035.006a1.396 1.396 0 0 0 1.298-.95l1.649-5.918h1.22l4.482 4.482a1.373 1.373 0 0 0 1.571.293 1.374 1.374 0 0 0 .782-1.254V1.374A1.375 1.375 0 0 0 13.483 0zm-2.071 18.067H7.76l-.487 1.745a.155.155 0 0 1-.295-.084l.649-2.33h1.854l1.932 1.93a.138.138 0 0 1-.065.234.137.137 0 0 1-.09-.033l-1.846-1.846zm-2.34-11.417h5.176v11.75l-5.176-5.176v-6.574zm8.356.545a1.86 1.86 0 0 0-1.22.443l-.497.43a.5.5 0 0 0 .656.76l.489-.422a.612.612 0 0 1 1.05.452v12.284a.612.612 0 0 1-1.05.451l-.487-.421a.5.5 0 1 0-.657.759l.496.429a1.861 1.861 0 0 0 3.092-1.218V8.413a1.862 1.862 0 0 0-1.872-1.818z"></path>
//             </svg>
//           </div>
//           <h2 className="text-lg font-bold leading-tight tracking-[-0.015em] hidden sm:block">
//             Coderacer
//           </h2>
//         </Link>

//         <nav className="hidden md:flex items-center gap-6">
//           <Link
//             href="/problems"
//             className="text-slate-900 dark:text-white text-sm font-medium leading-normal border-b-2 border-primary py-4 -my-4"
//           >
//             Problems
//           </Link>
//           <Link
//             href="/contest"
//             className="text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white text-sm font-medium leading-normal transition-colors"
//           >
//             Contest
//           </Link>
//           <Link
//             href="/discuss"
//             className="text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white text-sm font-medium leading-normal transition-colors"
//           >
//             Discuss
//           </Link>
//           <Link
//             href="/interview"
//             className="text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white text-sm font-medium leading-normal transition-colors"
//           >
//             Interview
//           </Link>
//           <Link
//             href="/store"
//             className="text-primary text-sm font-medium leading-normal flex items-center gap-1"
//           >
//             Store
//           </Link>
//         </nav>
//       </div>

//       <div className="flex flex-1 justify-end gap-4 md:gap-8 items-center">
//         <label className="hidden md:flex flex-col min-w-40 h-9! max-w-64">
//           <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-slate-100 dark:bg-surface-border overflow-hidden">
//             <div className="text-slate-400 dark:text-text-secondary flex items-center justify-center pl-3">
//               <span className="material-symbols-outlined text-[20px]">search</span>
//             </div>
//             <input
//               className="flex w-full min-w-0 flex-1 resize-none bg-transparent border-none text-slate-900 dark:text-white focus:outline-0 focus:ring-0 placeholder:text-slate-400 dark:placeholder:text-text-secondary px-3 text-sm font-normal leading-normal"
//               placeholder="Search"
//             />
//           </div>
//         </label>

//         <button className="hidden sm:flex items-center justify-center overflow-hidden rounded-lg h-9 px-4 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-bold uppercase tracking-wider transition-colors">
//           Premium
//         </button>

//         <div className="flex items-center gap-4">
//           <span className="material-symbols-outlined text-slate-500 dark:text-text-secondary cursor-pointer hover:text-slate-900 dark:hover:text-white transition-colors">
//             notifications
//           </span>
//           <div
//             className="bg-center bg-no-repeat bg-cover rounded-full size-8 cursor-pointer border border-slate-200 dark:border-surface-border"
//             style={{
//               backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuChvjuyEJDynudyZvPxQLtqc0N6aA_ygJFUoeJ9jVI1alwy17H16_GmTFaztlJPfzMCr-goTovK7xLUMJQjMB_wWaeEwziMEYDv2fb17VE-0xJTGvkwUxdF_s9j5__80-yQWNOgeZWV-JwXOChlbRr84yNY5Uzzsz338tbiCvUFp11xImPYgj2G1FIwBfInY8wmvOREe5Qo8ghQm3AiCJA2iRVlvulv_8ufyvyrGemvSN0dqiQBpDqpBNUKaRF4fxuFWNgDkiFkzhaE")'
//             }}
//           />
//         </div>
//       </div>
//     </header>
//   );
// }

// components/Header.tsx
import Link from 'next/link';
import Logo from '@/components/logo';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 flex items-center justify-between whitespace-nowrap border-b border-solid border-slate-200 dark:border-surface-border bg-white dark:bg-[#181b23] px-6 py-3 shadow-sm dark:shadow-none">
      <div className="flex items-center gap-8">
        <Logo />

        <nav className="hidden md:flex items-center gap-6">
          <Link
            href="/problems"
            className="text-slate-900 dark:text-white text-sm font-medium leading-normal border-b-2 border-primary py-4 -my-4"
          >
            Problems
          </Link>
          <Link
            href="/contest"
            className="text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white text-sm font-medium leading-normal transition-colors"
          >
            Contest
          </Link>
          <Link
            href="/discuss"
            className="text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white text-sm font-medium leading-normal transition-colors"
          >
            Discuss
          </Link>
          <Link
            href="/interview"
            className="text-slate-500 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white text-sm font-medium leading-normal transition-colors"
          >
            Interview
          </Link>
          <Link
            href="/store"
            className="text-primary text-sm font-medium leading-normal flex items-center gap-1"
          >
            Store
          </Link>
        </nav>
      </div>

      <div className="flex flex-1 justify-end gap-4 md:gap-8 items-center">
        <label className="hidden md:flex flex-col min-w-40 h-9! max-w-64">
          <div className="flex w-full flex-1 items-stretch rounded-lg h-full bg-slate-100 dark:bg-surface-border overflow-hidden">
            <div className="text-slate-400 dark:text-text-secondary flex items-center justify-center pl-3">
              <span className="material-symbols-outlined text-[20px]">search</span>
            </div>
            <input
              className="flex w-full min-w-0 flex-1 resize-none bg-transparent border-none text-slate-900 dark:text-white focus:outline-0 focus:ring-0 placeholder:text-slate-400 dark:placeholder:text-text-secondary px-3 text-sm font-normal leading-normal"
              placeholder="Search"
            />
          </div>
        </label>

        <button className="hidden sm:flex items-center justify-center overflow-hidden rounded-lg h-9 px-4 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-bold uppercase tracking-wider transition-colors">
          Premium
        </button>

        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-slate-500 dark:text-text-secondary cursor-pointer hover:text-slate-900 dark:hover:text-white transition-colors">
            notifications
          </span>
          <div
            className="bg-center bg-no-repeat bg-cover rounded-full size-8 cursor-pointer border border-slate-200 dark:border-surface-border"
            style={{
              backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuChvjuyEJDynudyZvPxQLtqc0N6aA_ygJFUoeJ9jVI1alwy17H16_GmTFaztlJPfzMCr-goTovK7xLUMJQjMB_wWaeEwziMEYDv2fb17VE-0xJTGvkwUxdF_s9j5__80-yQWNOgeZWV-JwXOChlbRr84yNY5Uzzsz338tbiCvUFp11xImPYgj2G1FIwBfInY8wmvOREe5Qo8ghQm3AiCJA2iRVlvulv_8ufyvyrGemvSN0dqiQBpDqpBNUKaRF4fxuFWNgDkiFkzhaE")'
            }}
          />
        </div>
      </div>
    </header>
  );
}