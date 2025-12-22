"use client"

// import { useState, useEffect, cache, Suspense, use } from "react"
// import { PanelLeftClose, PanelLeft } from "lucide-react"
// import { GetServerSideProps } from "next"
// import axios from "axios"
// import { BASE_URL } from "@/lib/constants"
// import useSWR from 'swr'
// import { DataTable } from "@/components/problem-list"

// export default function Home() {

//   return (
//     <div>
//       <DataTable />
//     </div>
//   )
// }

import Header from '@/components/header';
import Sidebar from '@/components/sidebar';
import DailyChallenge from '@/components/daily-challenge';
import ProblemTable from '@/components/problem-table';

export default function ProblemsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background-light dark:bg-background-dark">
      <Header />
      
      <div className="flex-1 w-full max-w-350 mx-auto p-4 md:p-6 lg:p-8 flex flex-col lg:flex-row gap-8">
        <Sidebar />
        
        <main className="flex-1 min-w-0 flex flex-col gap-6">
          {/* Top Section: Daily Challenge & Heading */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Heading Area */}
            <div className="md:col-span-2 flex flex-col justify-end gap-4 p-2">
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900 dark:text-white">
                Problems
              </h1>
              <div className="flex flex-wrap gap-3">
                <button className="flex items-center gap-2 px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg text-sm font-bold shadow-lg hover:shadow-xl transition-all transform active:scale-95">
                  <span className="material-symbols-outlined text-[18px]">shuffle</span>
                  Pick One
                </button>
                <div className="relative group">
                  <div className="flex items-center gap-2 px-4 py-2 bg-slate-200 dark:bg-surface-border text-slate-700 dark:text-text-secondary rounded-lg text-sm font-medium cursor-pointer hover:bg-slate-300 dark:hover:bg-[#3e4552] transition-colors">
                    <span className="material-symbols-outlined text-[18px]">calendar_month</span>
                    Session
                  </div>
                </div>
              </div>
            </div>
            
            <DailyChallenge />
          </div>

          {/* Problem List Controls */}
          <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center justify-between mt-2">
            <div className="relative flex-1 max-w-md">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="material-symbols-outlined text-slate-400 dark:text-text-secondary text-[20px]">
                  search
                </span>
              </div>
              <input
                className="block w-full pl-10 pr-3 py-2.5 border-none rounded-lg bg-slate-100 dark:bg-surface-border text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-text-secondary focus:ring-1 focus:ring-primary sm:text-sm"
                placeholder="Search questions by title or ID..."
                type="text"
              />
            </div>
            <div className="flex items-center gap-2 self-end sm:self-auto">
              <select className="form-select bg-slate-100 dark:bg-surface-border border-none text-slate-700 dark:text-text-secondary text-sm rounded-lg py-2.5 pl-3 pr-8 focus:ring-0 cursor-pointer">
                <option>Recommended</option>
                <option>Most Recent</option>
                <option>Most Votes</option>
              </select>
            </div>
          </div>

          <ProblemTable />
        </main>
      </div>
    </div>
  );
}
