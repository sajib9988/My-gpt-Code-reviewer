"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { Plus, SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api, type ChatReply, type Conversation, type Message } from "@/lib/api";

export function Chat({ projectId }: { projectId: string }) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeId, setActiveId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [pending, setPending] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const bottomRef = useRef<HTMLDivElement>(null);
    const justCreated = useRef<string | null>(null);

    useEffect(() => {
        api<Conversation[]>(`/projects/${projectId}/conversations`)
            .then((list) => { setConversations(list); setActiveId(list[0]?.id ?? null); })
            .catch(() => setConversations([]));
    }, [projectId]);

    useEffect(() => {
        if (!activeId) { setMessages([]); return; }
        if (justCreated.current === activeId) { justCreated.current = null; return; }
        api<Message[]>(`/conversations/${activeId}/messages`).then(setMessages).catch(() => setMessages([]));
    }, [activeId]);

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, pending]);

    async function newChat() {
        const conversation = await api<Conversation>(`/projects/${projectId}/conversations`, { method: "POST", body: JSON.stringify({}) });
        setConversations((items) => [conversation, ...items]);
        justCreated.current = conversation.id;
        setActiveId(conversation.id);
        setMessages([]);
        return conversation.id;
    }

    async function send(event?: FormEvent) {
        event?.preventDefault();
        const content = input.trim();
        if (!content || sending) return;
        setSending(true);
        setError("");
        setInput("");
        setPending(content);
        try {
            const id = activeId ?? (await newChat());
            const reply = await api<ChatReply>(`/conversations/${id}/chat`, { method: "POST", body: JSON.stringify({ content }) });
            setMessages((items) => [...items, reply.user_message, reply.assistant_message]);
            api<Conversation[]>(`/projects/${projectId}/conversations`).then(setConversations).catch(() => undefined);
        } catch (err) {
            setInput(content);
            setError(err instanceof Error ? err.message : "Message could not be sent");
        } finally {
            setPending("");
            setSending(false);
        }
    }

    function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
        if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); }
    }

    return (
        <div className="grid h-[calc(100vh-11rem)] gap-4 lg:grid-cols-[220px_1fr]">
            <aside className="hidden overflow-auto rounded-xl border border-[var(--line)] bg-[var(--panel)] p-3 lg:block">
                <Button variant="outline" className="mb-3 w-full" onClick={() => void newChat()}><Plus size={14} /> New chat</Button>
                {conversations.map((c) => (
                    <button key={c.id} onClick={() => setActiveId(c.id)} className={`mb-1 block w-full truncate rounded-md px-3 py-2 text-left text-xs ${c.id === activeId ? "bg-[var(--panel-raised)] text-white" : "text-[var(--muted)] hover:bg-white/5"}`}>{c.title}</button>
                ))}
            </aside>
            <section className="flex min-h-0 flex-col rounded-xl border border-[var(--line)] bg-[var(--panel)]">
                <div className="flex-1 space-y-4 overflow-auto p-5">
                    {!messages.length && !pending && <p className="pt-16 text-center text-sm text-[var(--muted)]">Ei project niye jekono kichu jiggesh koro.</p>}
                    {messages.map((m) => <Bubble key={m.id} role={m.role} content={m.content} />)}
                    {pending && <Bubble role="user" content={pending} />}
                    {sending && <p className="text-xs text-[var(--muted)]">Thinking...</p>}
                    <div ref={bottomRef} />
                </div>
                {error && <p className="mx-5 mb-2 rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-200">{error}</p>}
                <form onSubmit={send} className="flex items-end gap-2 border-t border-[var(--line)] p-3">
                    <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKeyDown} rows={2} placeholder="Message likho... (Enter = send, Shift+Enter = new line)" className="min-h-11 flex-1 resize-none rounded-md border border-[var(--line)] bg-[#0d141a] px-3 py-2 text-sm text-[var(--ink)] outline-none focus:border-[var(--cyan)]" />
                    <Button disabled={sending || !input.trim()} aria-label="Send"><SendHorizontal size={16} /></Button>
                </form>
            </section>
        </div>
    );
}

function Bubble({ role, content }: { role: string; content: string }) {
    const mine = role === "user";
    return (
        <div className={`flex ${mine ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] whitespace-pre-wrap break-words rounded-xl px-4 py-3 text-sm leading-6 ${mine ? "bg-[var(--cyan)] text-[#10201f]" : "border border-[var(--line)] bg-[var(--panel-raised)] text-[var(--ink)]"}`}>{content}</div>
        </div>
    );
}