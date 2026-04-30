import { cn } from "@/lib/utils";

export function Panel({
  children,
  className,
}: Readonly<{ children: React.ReactNode; className?: string }>) {
  return (
    <section className={cn("rounded-lg border border-border bg-white p-5 shadow-sm", className)}>
      {children}
    </section>
  );
}

export function PanelTitle({
  children,
  action,
}: Readonly<{ children: React.ReactNode; action?: React.ReactNode }>) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">{children}</h2>
      {action}
    </div>
  );
}
