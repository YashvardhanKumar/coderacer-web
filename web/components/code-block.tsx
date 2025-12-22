// components/shared/CodeBlock.tsx
import { ReactNode } from 'react';

interface CodeBlockProps {
  children: ReactNode;
  inline?: boolean;
}

export default function CodeBlock({ children, inline = false }: CodeBlockProps) {
  if (inline) {
    return (
      <code className="bg-surface-border px-1 py-0.5 rounded text-gray-200 font-mono text-xs">
        {children}
      </code>
    );
  }

  return (
    <pre className="bg-[#282e39] p-3 rounded text-gray-200 font-mono text-xs overflow-x-auto">
      <code>{children}</code>
    </pre>
  );
}