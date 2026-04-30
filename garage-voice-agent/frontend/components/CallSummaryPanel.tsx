import { ClipboardList } from "lucide-react";

import type { StructuredSummary } from "@/lib/types";
import { Badge } from "./ui/Badge";
import { Panel, PanelTitle } from "./ui/Panel";

function urgencyTone(urgency: StructuredSummary["urgency"]) {
  if (urgency === "high") return "red";
  if (urgency === "medium") return "amber";
  return "green";
}

export function CallSummaryPanel({
  summary,
}: Readonly<{ summary: StructuredSummary | null }>) {
  return (
    <Panel>
      <PanelTitle>
        <span className="flex items-center gap-2">
          <ClipboardList size={15} />
          Fiche appel
        </span>
      </PanelTitle>
      {!summary ? (
        <p className="text-sm text-muted">La fiche finale apparaitra apres la session ou via les donnees de demo.</p>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Badge tone="blue">{summary.intent}</Badge>
            <Badge tone={urgencyTone(summary.urgency)}>{summary.urgency}</Badge>
            <Badge>{summary.requested_action}</Badge>
            <Badge>{summary.appointment_status}</Badge>
          </div>
          <p className="text-sm leading-6 text-ink">{summary.summary_for_garage}</p>
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted">Client</dt>
              <dd className="font-medium">{summary.caller_name ?? "Non renseigne"}</dd>
            </div>
            <div>
              <dt className="text-muted">Telephone</dt>
              <dd className="font-medium">{summary.phone ?? "Non renseigne"}</dd>
            </div>
            <div>
              <dt className="text-muted">Vehicule</dt>
              <dd className="font-medium">
                {[summary.vehicle_make, summary.vehicle_model].filter(Boolean).join(" ") || "Non renseigne"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Prochaine action</dt>
              <dd className="font-medium">{summary.next_action}</dd>
            </div>
          </dl>
        </div>
      )}
    </Panel>
  );
}
