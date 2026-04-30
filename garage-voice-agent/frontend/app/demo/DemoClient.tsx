"use client";

import dynamic from "next/dynamic";

const VoiceDemoPanel = dynamic(
  () => import("@/components/VoiceDemoPanel").then((module) => module.VoiceDemoPanel),
  {
    ssr: false,
    loading: () => (
      <div className="rounded-lg border border-border bg-white p-6 text-sm text-muted">
        Chargement de la démo vocale...
      </div>
    ),
  },
);

export function DemoClient() {
  return <VoiceDemoPanel />;
}
