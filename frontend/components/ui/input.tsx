import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
    return (
        <input
            className={cn("h-11 w-full rounded-md border border-[var(--line)] bg-[#0d141a] px-3 text-sm text-[var(--ink)] outline-none placeholder:text-[#66727e] focus:border-[var(--cyan)]", className)}
            {...props}
        />
    );
}
