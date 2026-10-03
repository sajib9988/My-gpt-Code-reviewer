import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
    title: "Forge | AI Coding Workspace",
    description: "Project-based AI coding agent workspace",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
