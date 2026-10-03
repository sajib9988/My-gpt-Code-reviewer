import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Button({ className, variant = "solid", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "solid" | "ghost" | "outline" }) {
    return (
        <button
            className={cn(
                "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50",
                variant === "solid" && "bg-[var(--cyan)] text-[#10201f] hover:bg-[#91e1d3]",
                variant === "outline" && "border border-[var(--line)] bg-transparent text-[var(--ink)] hover:border-[var(--cyan)] hover:text-[var(--cyan)]",
                variant === "ghost" && "text-[var(--muted)] hover:bg-white/5 hover:text-[var(--ink)]",
                className,
            )}
            {...props}
        />
    );
}
