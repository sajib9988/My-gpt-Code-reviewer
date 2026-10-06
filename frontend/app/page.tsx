"use client";

import { useEffect, useState } from "react";
import type { ComponentType, FormEvent } from "react";
import { ArrowUpRight, Check, ChevronDown, CircleDot, FileCode2, FolderGit2, Github, LayoutDashboard, LogOut, Plus, Radar, RefreshCw, Search, ShieldCheck, Sparkles, TerminalSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, Repo, type Project, type ProjectFile, type Scan, type User } from "@/lib/api";

type AuthMode = "login" | "register";

const activity = [
    { icon: Check, text: "Workspace initialized", detail: "Ready for a project" },
    { icon: CircleDot, text: "GitHub connection", detail: "Waiting for authorization" },
    { icon: Radar, text: "Repository scanner", detail: "No scan started" },
];

export default function Home() {
    const [repoUrl, setRepoUrl] = useState("");
const [branch, setBranch] = useState("main");
const [repos, setRepos] = useState<Repo[]>([]);
const [tab, setTab] = useState<"chat" | "overview">("chat");
    const [user, setUser] = useState<User | null>(null);
    const [projects, setProjects] = useState<Project[]>([]);
    const [selected, setSelected] = useState<Project | null>(null);
    const [scan, setScan] = useState<Scan | null>(null);
    const [files, setFiles] = useState<ProjectFile[]>([]);
    const [authMode, setAuthMode] = useState<AuthMode>("login");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const [showCreate, setShowCreate] = useState(false);
    const [projectName, setProjectName] = useState("");

    async function loadWorkspace() {
        try {
            const current = await api<User>("/auth/me");
            const list = await api<Project[]>("/projects");
            setUser(current);
            setProjects(list);
            setSelected((previous) => list.find((project) => project.id === previous?.id) ?? list[0] ?? null);
        } catch {
            setUser(null);
        }
    }

    useEffect(() => { void loadWorkspace(); }, []);

    useEffect(() => {
        if (!selected) {
            setScan(null);
            setFiles([]);
            return;
        }
        void Promise.all([
            api<Scan>(`/projects/${selected.id}/scan`).then(setScan).catch(() => setScan(null)),
            api<ProjectFile[]>(`/projects/${selected.id}/files`).then(setFiles).catch(() => setFiles([])),
        ]);
    }, [selected]);

    async function handleAuth(event: FormEvent) {
        event.preventDefault();
        setBusy(true);
        setMessage("");
        try {
            const endpoint = authMode === "login" ? "/auth/login" : "/auth/register";
            await api<User>(endpoint, { method: "POST", body: JSON.stringify({ email, password }) });
            await loadWorkspace();
        } catch (error) {
            setMessage(error instanceof Error ? error.message : "Unable to authenticate");
        } finally {
            setBusy(false);
        }
    }

    async function createProject(event: FormEvent) {
        event.preventDefault();
        if (!projectName.trim()) return;
        setBusy(true);
        try {
            const project = await api<Project>("/projects", { method: "POST", body: JSON.stringify({ name: projectName }) });
            setProjects((items) => [project, ...items]);
            setSelected(project);
            setProjectName("");
            setShowCreate(false);
        } catch (error) {
            setMessage(error instanceof Error ? error.message : "Unable to create project");
        } finally {
            setBusy(false);
        }
    }

    async function scanProject() {
        if (!selected) return;
        setBusy(true);
        setMessage("");
        try {
            const result = await api<Scan>(`/projects/${selected.id}/scan`, { method: "POST" });
            setScan(result);
            setFiles(await api<ProjectFile[]>(`/projects/${selected.id}/files`));
        } catch (error) {
            setMessage(error instanceof Error ? error.message : "Scan could not start");
        } finally {
            setBusy(false);
        }
    }

    async function connectGitHub() {
        try {
            const result = await api<{ authorization_url: string }>("/github/connect", { method: "POST" });
            window.location.href = result.authorization_url;
        } catch (error) {
            setMessage(error instanceof Error ? error.message : "GitHub is not configured");
        }
    }

    async function logout() {
        await api<void>("/auth/logout", { method: "POST" }).catch(() => undefined);
        setUser(null);
        setProjects([]);
        setSelected(null);
    }

    if (!user) {
        return (
            <main className="flex min-h-screen items-center justify-center px-5 py-12">
                <div className="grid w-full max-w-5xl overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--panel)] shadow-2xl shadow-black/30 lg:grid-cols-[1.1fr_0.9fr]">
                    <section className="hidden border-r border-[var(--line)] p-12 lg:block">
                        <div className="mb-20 flex items-center gap-3 text-sm font-bold tracking-[0.2em] text-[var(--cyan)]"><TerminalSquare size={18} /> FORGE</div>
                        <p className="mb-5 max-w-md text-sm uppercase tracking-[0.18em] text-[var(--amber)]">Project-based coding intelligence</p>
                        <h1 className="max-w-lg text-5xl font-semibold leading-[1.02] tracking-[-0.04em] text-white">Make the codebase your conversation.</h1>
                        <p className="mt-7 max-w-md font-sans text-base leading-7 text-[var(--muted)]">Connect a repository, build durable context, and move from a task to a reviewed change without losing the thread.</p>
                        <div className="mt-20 flex items-center gap-8 text-xs text-[var(--muted)]"><span className="flex items-center gap-2"><ShieldCheck size={16} className="text-[var(--cyan)]" /> Isolated projects</span><span className="flex items-center gap-2"><Sparkles size={16} className="text-[var(--amber)]" /> Agent-ready</span></div>
                    </section>
                    <section className="p-7 sm:p-12">
                        <div className="mb-10 flex items-center gap-3 text-sm font-bold tracking-[0.2em] text-[var(--cyan)] lg:hidden"><TerminalSquare size={18} /> FORGE</div>
                        <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">{authMode === "login" ? "Welcome back" : "Create workspace access"}</p>
                        <h2 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-white">{authMode === "login" ? "Sign in to Forge" : "Start building"}</h2>
                        <form className="mt-8 space-y-4" onSubmit={handleAuth}>
                            <label className="block text-xs text-[var(--muted)]">Email<Input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2" /></label>
                            <label className="block text-xs text-[var(--muted)]">Password<Input type="password" required minLength={authMode === "register" ? 12 : 1} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2" /></label>
                            {message && <p className="rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-200">{message}</p>}
                            <Button className="mt-2 w-full" disabled={busy}>{busy ? "Connecting..." : authMode === "login" ? "Enter workspace" : "Create account"}<ArrowUpRight size={16} /></Button>
                        </form>
                        <button className="mt-6 w-full text-center text-xs text-[var(--muted)] hover:text-[var(--cyan)]" onClick={() => { setAuthMode(authMode === "login" ? "register" : "login"); setMessage(""); }}>{authMode === "login" ? "Need an account? Register" : "Already have access? Sign in"}</button>
                    </section>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen">
            <header className="flex h-16 items-center justify-between border-b border-[var(--line)] bg-[#0c1218]/90 px-5 backdrop-blur sm:px-8">
                <div className="flex items-center gap-3"><span className="flex h-8 w-8 items-center justify-center rounded-md bg-[var(--cyan)] text-[#10201f]"><TerminalSquare size={17} /></span><span className="text-sm font-bold tracking-[0.2em] text-white">FORGE</span><span className="hidden border-l border-[var(--line)] pl-4 text-xs text-[var(--muted)] sm:block">AI CODING WORKSPACE</span></div>
                <div className="flex items-center gap-3"><span className="hidden text-xs text-[var(--muted)] sm:block">{user.email}</span><Button variant="ghost" aria-label="Log out" onClick={logout}><LogOut size={16} /></Button></div>
            </header>
            <div className="mx-auto grid max-w-[1500px] lg:grid-cols-[260px_1fr]">
                <aside className="border-b border-[var(--line)] p-5 lg:min-h-[calc(100vh-4rem)] lg:border-r lg:border-b-0">
                    <div className="mb-7 flex items-center justify-between"><span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--muted)]">Projects</span><Button variant="ghost" className="h-7 w-7 p-0" aria-label="Create project" onClick={() => setShowCreate(true)}><Plus size={16} /></Button></div>
                    <div className="space-y-1">{projects.map((project) => <button key={project.id} onClick={() => setSelected(project)} className={`flex w-full items-center gap-3 rounded-md px-3 py-3 text-left text-sm ${selected?.id === project.id ? "bg-[var(--panel-raised)] text-white" : "text-[var(--muted)] hover:bg-white/5 hover:text-white"}`}><FolderGit2 size={16} className={selected?.id === project.id ? "text-[var(--cyan)]" : ""} /><span className="min-w-0 flex-1 truncate">{project.name}</span>{selected?.id === project.id && <ChevronDown size={14} />}</button>)}</div>
                    {!projects.length && <p className="text-xs leading-5 text-[var(--muted)]">No projects yet. Create one to begin.</p>}
                    <div className="mt-10 border-t border-[var(--line)] pt-5"><p className="mb-3 text-[10px] uppercase tracking-[0.18em] text-[var(--muted)]">Workspace</p><div className="space-y-1 text-sm text-[var(--muted)]"><div className="flex items-center gap-3 rounded-md bg-white/5 px-3 py-2 text-white"><LayoutDashboard size={15} /> Overview</div><div className="flex items-center gap-3 px-3 py-2"><Search size={15} /> Code search</div></div></div>
                </aside>
                <section className="min-w-0 p-5 sm:p-8">
                    {!selected ? <EmptyState onCreate={() => setShowCreate(true)} /> : <ProjectOverview project={selected} scan={scan} files={files} busy={busy} message={message} onScan={scanProject} onConnect={connectGitHub} />}
                </section>
            </div>
            {showCreate && <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/60 px-5"><form onSubmit={createProject} className="w-full max-w-md rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-2xl"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold text-white">New project</h2><Button type="button" variant="ghost" className="h-8 w-8 p-0" onClick={() => setShowCreate(false)}>×</Button></div><p className="mt-2 text-xs text-[var(--muted)]">A private context boundary for one repository and its agents.</p><Input autoFocus value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="Project name" className="mt-5" /><Button className="mt-4 w-full" disabled={busy}>Create project</Button></form></div>}
        </main>
    );
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
    return <div className="animate-rise flex min-h-[65vh] flex-col items-center justify-center text-center"><div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl border border-[var(--line)] bg-[var(--panel)] text-[var(--cyan)]"><FolderGit2 size={24} /></div><p className="text-xs uppercase tracking-[0.18em] text-[var(--amber)]">First context boundary</p><h1 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-white">Create a project to begin.</h1><p className="mt-3 max-w-md font-sans text-sm leading-6 text-[var(--muted)]">Every repository, conversation, run, and memory stays isolated inside its project.</p><Button className="mt-7" onClick={onCreate}><Plus size={16} /> New project</Button></div>;
}

function ProjectOverview({ project, scan, files, busy, message, onScan, onConnect }: { project: Project; scan: Scan | null; files: ProjectFile[]; busy: boolean; message: string; onScan: () => void; onConnect: () => void }) {
    return <div className="animate-rise"><div className="flex flex-col justify-between gap-5 border-b border-[var(--line)] pb-7 sm:flex-row sm:items-end"><div><p className="text-xs uppercase tracking-[0.16em] text-[var(--cyan)]">Project / Overview</p><h1 className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-white">{project.name}</h1><p className="mt-2 max-w-xl font-sans text-sm text-[var(--muted)]">{project.description || "Repository context, agent activity, and changes in one place."}</p></div><div className="flex gap-2"><Button variant="outline" onClick={onConnect}><Github size={16} /> Connect GitHub</Button><Button onClick={onScan} disabled={busy || !project.repository_url}><RefreshCw size={16} className={busy ? "animate-spin" : ""} /> Scan repository</Button></div></div>{message && <p className="mt-5 rounded-md border border-[var(--amber)]/30 bg-[var(--amber)]/10 px-4 py-3 text-xs text-[var(--amber)]">{message}</p>}<div className="mt-7 grid gap-4 sm:grid-cols-3"><Metric label="Framework" value={scan?.framework || "Awaiting scan"} icon={Radar} /><Metric label="Indexed files" value={scan ? String(scan.files_count) : "—"} icon={FileCode2} /><Metric label="Branch" value={project.branch} icon={GitBranchIcon} /></div><div className="mt-7 grid gap-5 xl:grid-cols-[1.15fr_0.85fr]"><section className="rounded-xl border border-[var(--line)] bg-[var(--panel)]"><div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-4"><div><h2 className="text-sm font-semibold text-white">Repository activity</h2><p className="mt-1 text-xs text-[var(--muted)]">The project context pipeline</p></div><span className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted)]">Live</span></div><div className="space-y-1 p-3">{activity.map(({ icon: Icon, text, detail }) => <div key={text} className="flex items-center gap-3 rounded-md px-2 py-3"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#20332f] text-[var(--cyan)]"><Icon size={14} /></span><div className="min-w-0"><p className="text-xs text-white">{text}</p><p className="mt-1 text-[11px] text-[var(--muted)]">{detail}</p></div></div>)}</div></section><section className="rounded-xl border border-[var(--line)] bg-[var(--panel)]"><div className="border-b border-[var(--line)] px-5 py-4"><h2 className="text-sm font-semibold text-white">Indexed files</h2><p className="mt-1 text-xs text-[var(--muted)]">{files.length ? "Latest repository metadata" : "Run a scan to populate context"}</p></div><div className="max-h-64 overflow-auto p-3">{files.slice(0, 12).map((file) => <div key={file.path} className="flex items-center gap-3 rounded px-2 py-2 text-xs text-[var(--muted)] hover:bg-white/5"><FileCode2 size={14} className="shrink-0 text-[var(--cyan)]" /><span className="truncate">{file.path}</span></div>)}</div></section></div></div>;
}

function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: ComponentType<{ size?: number }> }) {
    return <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5"><div className="flex items-center gap-2 text-[var(--muted)]"><Icon size={15} /><span className="text-[10px] uppercase tracking-[0.16em]">{label}</span></div><p className="mt-4 truncate text-lg font-semibold text-white">{value}</p></div>;
}

function GitBranchIcon(props: { size?: number }) {
    return <svg aria-hidden="true" fill="none" height={props.size ?? 16} viewBox="0 0 24 24" width={props.size ?? 16} stroke="currentColor" strokeWidth="2"><circle cx="6" cy="6" r="3" /><circle cx="18" cy="18" r="3" /><path d="M6 9v3a6 6 0 0 0 6 6h3" /><circle cx="18" cy="6" r="3" /><path d="M9 6h6" /></svg>;
}
