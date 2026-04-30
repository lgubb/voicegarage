import { forwardRef } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, disabled = false, variant = "primary", ...props }, ref) => {
    const variants = {
      primary: "bg-ink text-white hover:bg-black",
      secondary: "border border-border bg-white text-ink hover:bg-surface",
      ghost: "text-muted hover:bg-surface hover:text-ink",
      danger: "bg-red-600 text-white hover:bg-red-700",
    };
    return (
      <button
        ref={ref}
        disabled={Boolean(disabled)}
        className={cn(
          "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
          variants[variant],
          className,
        )}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
