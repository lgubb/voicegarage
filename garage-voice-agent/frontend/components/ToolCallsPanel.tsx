import { Braces } from "lucide-react";

import type { ToolCall } from "@/lib/types";
import { Badge } from "./ui/Badge";
import { Panel, PanelTitle } from "./ui/Panel";

export function ToolCallsPanel({ toolCalls }: Readonly<{ toolCalls: ToolCall[] }>) {
  return (
    <Panel>
      <PanelTitle>
        <span className="flex items-center gap-2">
          <Braces size={15} />
          Tools appeles
        </span>
      </PanelTitle>
      {toolCalls.length === 0 ? (
        <p className="text-sm text-muted">Aucun tool appele pour le moment.</p>
      ) : (
        <div className="space-y-3">
          {toolCalls.map((tool, index) => (
            <div key={`${tool.name}-${index}`} className="rounded-md border border-border p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <code className="text-sm font-semibold text-ink">{tool.name}</code>
                <Badge tone={tool.status === "ok" ? "green" : "amber"}>{tool.status ?? "ok"}</Badge>
              </div>
              <pre className="overflow-x-auto rounded bg-slate-950 p-3 text-xs text-slate-100">
                {JSON.stringify(tool.arguments ?? {}, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
