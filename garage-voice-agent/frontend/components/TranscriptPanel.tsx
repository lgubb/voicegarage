import { MessageSquareText } from "lucide-react";

import type { TranscriptMessage } from "@/lib/types";
import { Panel, PanelTitle } from "./ui/Panel";

export function TranscriptPanel({ transcript }: Readonly<{ transcript: TranscriptMessage[] }>) {
  return (
    <Panel>
      <PanelTitle>
        <span className="flex items-center gap-2">
          <MessageSquareText size={15} />
          Transcript
        </span>
      </PanelTitle>
      <div className="space-y-3">
        {transcript.map((message, index) => (
          <div key={`${message.role}-${index}`} className="rounded-md bg-surface p-3">
            <div className="mb-1 text-xs font-medium uppercase text-muted">{message.role}</div>
            <p className="text-sm leading-6 text-ink">{message.text}</p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
