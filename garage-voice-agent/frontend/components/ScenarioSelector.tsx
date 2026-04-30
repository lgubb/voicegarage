"use client";

import { Car, CircleAlert, ClipboardCheck, Wrench } from "lucide-react";

import type { Scenario } from "@/lib/types";
import { cn } from "@/lib/utils";

const scenarios: Array<{ value: Scenario; label: string; icon: React.ElementType }> = [
  { value: "revision", label: "Révision", icon: ClipboardCheck },
  { value: "pneus", label: "Pneus", icon: Car },
  { value: "carrosserie", label: "Carrosserie", icon: Wrench },
  { value: "panne_urgente", label: "Panne urgente", icon: CircleAlert },
  { value: "custom", label: "Personnalisé", icon: ClipboardCheck },
];

export function ScenarioSelector({
  value,
  onChange,
}: Readonly<{ value: Scenario; onChange: (scenario: Scenario) => void }>) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {scenarios.map((scenario) => {
        const Icon = scenario.icon;
        const selected = scenario.value === value;
        return (
          <button
            key={scenario.value}
            type="button"
            onClick={() => onChange(scenario.value)}
            className={cn(
              "flex h-24 flex-col items-start justify-between rounded-lg border p-4 text-left text-sm transition",
              selected
                ? "border-ink bg-ink text-white"
                : "border-border bg-white text-ink hover:border-slate-300 hover:bg-surface",
            )}
          >
            <Icon size={17} />
            <span className="font-medium">{scenario.label}</span>
          </button>
        );
      })}
    </div>
  );
}
