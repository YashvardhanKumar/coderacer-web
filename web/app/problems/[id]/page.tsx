// app/problems/[id]/page.tsx
"use client";
import ProblemHeader from '@/components/problem/header';
import ProblemDescription from '@/components/problem/problem-description';
import CodeEditor from '@/components/problem/code-editor';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import useSWR from 'swr';
import { BASE_URL } from '@/lib/constants';
import { useParams } from 'next/navigation';
import {Loader} from '@/components/loader';

const fetcher = (url: string) => fetch(url).then((r) => r.json())

export default function ProblemDetailPage() {
  const { id } = useParams();
  const { data, error, isLoading } = useSWR(`${BASE_URL}/api/problems/${id}/`, fetcher)
  const { data: userData, error: userError, isLoading: userIsLoading } = useSWR(`${BASE_URL}/auth/users/me/`, fetcher)
  if(isLoading || userIsLoading) {
    return <Loader />;
  }
  if(error || userError) {
    return <div>Error loading problem.</div>
  }
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-background-dark">
      <ProblemHeader />

      <ResizablePanelGroup direction="horizontal">
        <ProblemDescription problem={data} />
        <ResizableHandle />
        <CodeEditor user={userData} problem={data} />
      </ResizablePanelGroup>
    </div>
  );
}