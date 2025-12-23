// components/problem/CodeEditor.tsx
"use client";

import EditorToolbar from "./editor-toolbar";
import TestPanel from "./test-panel";
import Editor from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "../ui/resizable";
import { Language, Problem, User } from "@/lib/models";
import { useEffect, useState } from "react";

interface Props {
  problem: Problem;
  user: User;
}

export default function CodeEditor({ problem, user }: Props) {
  const [code, setCode] = useState<string>();
  console.log(problem.codeblocks);

  useEffect(() => {
    if (
      localStorage.getItem(problem.id.toString()) &&
      localStorage.getItem("preferredLanguage") ===
        (user.default_lang ?? Language.CPP).toString()
    ) {
      setCode(localStorage.getItem(problem.id.toString()) ?? "");
      return;
    }
    setCode(
      problem.codeblocks.filter(
        (e) => e.language === (user.default_lang ?? Language.CPP)
      )[0]?.block ?? ""
    );
  }, [problem, user]);

  useEffect(() => {
    localStorage.setItem(
      "preferredLanguage",
      (user.default_lang ?? Language.CPP).toString()
    );
    localStorage.setItem(problem.id.toString(), code ?? "");
  }, [code]);

  return (
    <ResizablePanel defaultSize={50}>
      <ResizablePanelGroup
        direction="vertical"
        className="flex-1 flex flex-col bg-editor-bg relative min-w-100 overflow-y-hidden"
      >
        <ResizablePanel defaultSize={60}>
          <EditorToolbar />
          <Editor
            height="90vh"
            defaultLanguage={(user.default_lang ?? Language.CPP).toLowerCase()}
            defaultValue={code}
            theme="vs-dark"
            onChange={(value) => setCode(value ?? "")}
          />
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel defaultSize={40}>
          <TestPanel
            problem={problem}
            user={user}
            code={code}
            language={user.default_lang ?? Language.CPP}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </ResizablePanel>
  );
}
