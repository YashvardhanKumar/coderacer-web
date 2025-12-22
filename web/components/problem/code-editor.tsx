// components/problem/CodeEditor.tsx
'use client';

import EditorToolbar from './editor-toolbar';
import TestPanel from './test-panel';
import Editor from '@monaco-editor/react';
import * as monaco from 'monaco-editor';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '../ui/resizable';
import { Problem, User } from '@/lib/models';

interface Props {
  problem: Problem
  user: User
}

export default function CodeEditor({ problem, user }: Props) {
  console.log(problem.codeblocks);
  
  return (
    <ResizablePanel defaultSize={50}>
      <ResizablePanelGroup direction="vertical" className="flex-1 flex flex-col bg-editor-bg relative min-w-100 overflow-y-hidden">
        <ResizablePanel defaultSize={60}>
          <EditorToolbar />
          <Editor height="90vh" defaultLanguage={((user.default_lang) ?? "CPP").toLowerCase()} defaultValue={problem.codeblocks.filter(e => e.language === (user.default_lang ?? "CPP"))[0]?.block} theme='vs-dark' />
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel defaultSize={40}>
          <TestPanel />
        </ResizablePanel>
      </ResizablePanelGroup>
    </ResizablePanel>
  );
}
