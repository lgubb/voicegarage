import Link from "next/link";
import { ArrowRight } from "lucide-react";

import type { CallRecord, StructuredSummary } from "@/lib/types";
import { Badge } from "./ui/Badge";

function urgencyTone(urgency?: StructuredSummary["urgency"]) {
  if (urgency === "high") return "red";
  if (urgency === "medium") return "amber";
  if (urgency === "low") return "green";
  return "default";
}

export function CallRecordCard({ call }: Readonly<{ call: CallRecord }>) {
  const summary = call.structured_summary;
  const vehicle = [summary?.vehicle_make, summary?.vehicle_model].filter(Boolean).join(" ");
  return (
    <article className="rounded-lg border border-border bg-white p-5 shadow-sm transition hover:border-slate-300">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-ink">{summary?.caller_name ?? "Client non renseigne"}</h2>
          <p className="mt-1 text-sm text-muted">{vehicle || "Vehicule non renseigne"}</p>
        </div>
        <Badge tone={urgencyTone(summary?.urgency)}>{summary?.urgency ?? "pending"}</Badge>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge tone="blue">{summary?.intent ?? call.scenario}</Badge>
        <Badge>{summary?.requested_action ?? call.status}</Badge>
        <Badge>{summary?.appointment_status ?? "not_requested"}</Badge>
      </div>
      <p className="mt-4 line-clamp-2 text-sm leading-6 text-muted">
        {summary?.summary_for_garage ?? "Session creee. La fiche sera completee apres l'appel."}
      </p>
      <Link
        href={`/calls/${call.id}`}
        className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-ink hover:text-accent"
      >
        Voir detail
        <ArrowRight size={15} />
      </Link>
    </article>
  );
}
