// components/problem/TestPanel.tsx
"use client";

import { CODE_RUNNER_URL } from "@/lib/constants";
import {
  DataType,
  Language,
  LanguageCodes,
  Problem,
  RunCodePayload,
  TestcaseList,
  User,
} from "@/lib/models";
import apiClient from "@/lib/utils";
import { AxiosResponse } from "axios";
import { useState } from "react";

interface Props {
  problem: Problem;
  user: User;
  language?: Language;
  code?: string;
}

export default function TestPanel({
  problem,
  user,
  language = Language.PYTHON,
  code,
}: Props) {
  const [activeTab, setActiveTab] = useState("testcase");
  const [activeCase, setActiveCase] = useState(0);
  const [runData, setRunData] = useState<any>();
  const [responseData, setResponseData] = useState<any>();

  const testcases = problem.testcases.filter((e) => e.display_testcase == true);

  const runCode = async () => {
    const codeblock = problem.codeblocks.filter(
      (e) => e.language === language
    )[0];

    code =
      codeblock.imports +
      "\n\n" +
      (code ?? codeblock.block) +
      "\n\n" +
      codeblock.runner_code;
    const response = await apiClient.post<
      any,
      AxiosResponse<any, any, {}>,
      RunCodePayload
    >("/engine/run/", {
      problem_id: problem.id,
      source_code: code ?? "",
      language_id: LanguageCodes[language],
      number_of_runs: 1,
      enable_per_process_and_thread_time_limit: true,
      enable_per_process_and_thread_memory_limit: true,
      enable_network: true,
    });
    setRunData(response.data);
    console.log(response.data);

    // WARNING: For POST requests, body is set to null by browsers.
    if (Array.isArray(response.data)) {
      setResponseData(response.data);
      console.table(response.data);
      setActiveTab("result");
    }
  };

  const opTobfyarr = ( output_type: DataType, output?: string) => {
    return output?.trim().split("\n").map((line) => output_type === DataType.STRING ? line.trim() : parseInt(line.trim())).toString();
  }

  return (
    <div className="h-full border-t border-[#282e39] bg-[#1a1a1a] flex flex-col shrink-0">
      {/* Panel Header */}
      <div className="flex items-center px-4 py-2 gap-4">
        <button
          onClick={() => setActiveTab("testcase")}
          className={`flex items-center gap-2 text-xs font-bold border-b-2 pb-2 transition-colors ${
            activeTab === "testcase"
              ? "text-white border-primary"
              : "text-gray-500 hover:text-white border-transparent"
          }`}
        >
          <span className="material-symbols-outlined text-[16px] text-green-500">
            check_circle
          </span>
          Testcase
        </button>
        <button
          onClick={() => setActiveTab("result")}
          className={`flex items-center gap-2 text-xs font-bold border-b-2 pb-2 transition-colors ${
            activeTab === "result"
              ? "text-white border-primary"
              : "text-gray-500 hover:text-white border-transparent"
          }`}
        >
          Test Result
        </button>
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-14">
        {activeTab === "testcase" && (
          <>
            <div className="flex gap-2 mb-4 mt-2">
              {testcases.map((_, index) => (
                <button
                  onClick={() => setActiveCase(index)}
                  className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    activeCase === index
                      ? "bg-[#282e39] text-white"
                      : "text-gray-400 hover:text-white hover:bg-[#282e39]"
                  }`}
                >
                  Case {index + 1}
                </button>
              ))}

              <button className="text-gray-400 hover:text-white hover:bg-[#282e39] size-7 flex items-center justify-center rounded-md transition-colors">
                <span className="material-symbols-outlined text-[18px]">
                  add
                </span>
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {testcases &&
                testcases
                  .at(activeCase)
                  ?.input.replaceAll("\r\n", "\n")
                  .split("\n")
                  .map((line) => {
                    const [key, value] = line.split("=", 2);
                    return (
                      <div>
                        <p className="text-gray-400 mb-1">{key} = </p>
                        <div className="bg-[#282e39] p-2 rounded text-white border border-gray-700">
                          {value}
                        </div>
                      </div>
                    );
                  })}
            </div>
          </>
        )}
        {activeTab === "result" && (
          <div className="text-gray-400 text-sm">
            {runData ? (
              <div className="space-y-3 pb-3">
                <div>{runData[activeCase].status.description}</div>
                <div className="flex gap-2 mb-4 mt-2">
                  {testcases.map((_, index) => (
                    <button
                      onClick={() => setActiveCase(index)}
                      className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        activeCase === index
                          ? "bg-[#282e39] text-white"
                          : "text-gray-400 hover:text-white hover:bg-[#282e39]"
                      }`}
                    >
                      Case {index + 1}
                    </button>
                  ))}
                </div>
                <div className="space-y-3 font-mono text-xs">
                  <p className="text-gray-400 mb-1">Input</p>
                  {testcases[activeCase].input
                    .replaceAll("\r\n", "\n")
                    .split("\n")
                    .map((line) => {
                      const [key, value] = line.split("=", 2);
                      return (
                        <div className="bg-[#282e39] p-2 rounded text-white border border-gray-700">
                          <p className="text-gray-400 mb-1">{key} = </p>
                          <div>{value}</div>
                        </div>
                      );
                    })}
                </div>
                <div className="space-y-3 font-mono text-xs">
                  <p className="text-gray-400 mb-1">Output</p>
                  {Array.isArray(responseData) && (
                    <div className="bg-[#282e39] p-2 rounded text-white border border-gray-700">
                      <div>[{opTobfyarr(testcases[activeCase].output_type, responseData[activeCase]?.stdout)}]</div>
                    </div>
                  )}
                </div>
                <div className="space-y-3 font-mono text-xs">
                  <p className="text-gray-400 mb-1">Expected Output</p>
                  {Array.isArray(responseData) && (
                    <div className="bg-[#282e39] p-2 rounded text-white border border-gray-700">
                      <div>[{opTobfyarr(testcases[activeCase].output_type, responseData[activeCase]?.expected_output)}]</div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div>Run code first to show</div>
            )}
          </div>
        )}
      </div>

      {/* Run/Submit Footer */}
      <div className="absolute bottom-0 w-full p-2 flex justify-between items-center bg-[#1a1a1a] border-t border-surface-border">
        <button className="text-gray-400 hover:text-white text-xs px-3 py-1.5 rounded hover:bg-[#282e39] flex items-center gap-2 transition-colors">
          <span className="material-symbols-outlined text-[18px]">
            terminal
          </span>
          Console
        </button>
        <div className="flex gap-2">
          <button className="btn-primary" onClick={() => runCode()}>
            Run
          </button>
          <button className="btn-secondary">Submit</button>
        </div>
      </div>
    </div>
  );
}
