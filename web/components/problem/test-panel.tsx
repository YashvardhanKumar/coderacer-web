// components/problem/TestPanel.tsx
"use client";

import {
  Language,
  LanguageCodes,
  Problem,
  Testcase,
  TestcaseList,
  User,
} from "@/lib/models";
import { log } from "console";
import { validateHeaderValue } from "http";
import { useEffect, useState } from "react";

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
  const [activeCase, setActiveCase] = useState(1);
  const [variavles, setVariables] = useState<Record<string, string>>({});

  const testcases = problem.testcases;

  const runCode = (testcase: TestcaseList) => {
    // WARNING: For POST requests, body is set to null by browsers.

    const testCases = Object.values(rawTestCases(testcase)).join("\n");
    const output = parseObj(JSON.parse(testcase.output), false);
    var data = JSON.stringify({
      source_code: code,
      language_id: LanguageCodes[language],
      number_of_runs: "1",
      stdin: testCases,
      expected_output: output,
      cpu_time_limit: "5",
      cpu_extra_time: "1",
      wall_time_limit: "10",
      memory_limit: "128000",
      stack_limit: "64000",
      max_processes_and_or_threads: "60",
      enable_per_process_and_thread_time_limit: true,
      enable_per_process_and_thread_memory_limit: true,
      max_file_size: "1024",
      enable_network: true,
    });

    var xhr = new XMLHttpRequest();
    // xhr.withCredentials = true;

    xhr.addEventListener("readystatechange", function () {
      if (this.readyState === 4) {
        console.log(this.responseText);
        alert((this.response));
      }
    });

    xhr.open("POST", "http://10.98.182.37:2358/submissions?wait=true");
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.send(data);
  };

  const parseObj = (
    value: object | number | string,
    addLength: boolean = true
  ): string => {
    if (typeof value === "object" && Array.isArray(value)) {
      const parsedArr = value.map((v) => {
        const parsedValue = parseObj(v);
        return parsedValue;
      });
      const final = `${
        addLength ? `${parsedArr.length}\n` : ""
      }${parsedArr.join(" ")}\n`;
      return final;
    } else {
      return `${value}`;
    }
  };

  const rawTestCases = (testcases: TestcaseList) => {
    const vars = testcases.input.replaceAll("\r\n", "\n").split("\n");
    let parsedVariables: { [key: string]: string } = {};

    vars.forEach((v) => {
      const [key, value] = v.split("=", 2);
      if (key && value) {
        parsedVariables[key.trim()] = parseObj(JSON.parse(value.trim()));
      }
      console.table([key, JSON.parse(value.trim())]);
    });

    return parsedVariables;
  };

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
            <div className="flex gap-2 mb-4">
              {testcases.slice(0, 3).map((_, index) => (
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
              {testcases[activeCase].input
                .replaceAll("\r\n", "\n")
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
            Run your code to see test results here
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
          <button className="btn-primary" onClick={() => testcases.forEach((tc) => runCode(tc))}>
            Run
          </button>
          <button className="btn-secondary">Submit</button>
        </div>
      </div>
    </div>
  );
}
