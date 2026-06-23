import type { ChatMessage, DocumentOut, Session, User } from "@/types"

function safeGet(key: string): string | null {
  try {
    return window.localStorage ? window.localStorage.getItem(key) : null
  } catch {
    return null
  }
}

function safeSet(key: string, value: string) {
  try {
    window.localStorage?.setItem(key, value)
  } catch {
    /* sandboxed iframe — ignore */
  }
}

function safeRemove(key: string) {
  try {
    window.localStorage?.removeItem(key)
  } catch {
    /* ignore */
  }
}

// API base: explicit override wins; otherwise same-origin "/api" (FastAPI / the Space).
// When the static UI is served from GitHub Pages, point at the hosted Space backend.
export const API_BASE: string =
  (window as unknown as { BANGLARAG_API_BASE?: string }).BANGLARAG_API_BASE ||
  safeGet("banglaragApiBase") ||
  (location.hostname.endsWith("github.io")
    ? "https://mdfaisalsheikh-banglarag.hf.space/api"
    : "/api")

interface RequestOptions {
  method?: string
  body?: unknown
  token?: string | null
}

export async function apiFetch<T = unknown>(
  path: string,
  { method = "GET", body, token }: RequestOptions = {}
): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers["Content-Type"] = "application/json"
  if (token) headers["Authorization"] = "Bearer " + token

  const res = await fetch(API_BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || res.statusText || "Request failed")
  }
  return (res.status === 204 ? null : await res.json()) as T
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const form = new URLSearchParams({ username: email, password })
  const res = await fetch(API_BASE + "/auth/login", { method: "POST", body: form })
  if (!res.ok) throw new Error("ভুল ইমেইল বা পাসওয়ার্ড")
  return res.json()
}

export async function register(email: string, password: string): Promise<User> {
  return apiFetch<User>("/auth/register", { method: "POST", body: { email, password } })
}

export async function me(token: string): Promise<User> {
  return apiFetch<User>("/auth/me", { token })
}

export interface ChatResponse {
  answer: string
  citations: ChatMessage["citations"]
  conversation_id: number | null
  grounded: boolean
}

export async function sendChat(
  question: string,
  conversationId: number | null,
  token: string
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    token,
    body: { question, conversation_id: conversationId },
  })
}

export async function listDocuments(token: string): Promise<DocumentOut[]> {
  return apiFetch<DocumentOut[]>("/admin/documents", { token })
}

export async function addDocument(title: string, text: string, token: string): Promise<DocumentOut> {
  return apiFetch<DocumentOut>("/admin/documents", {
    method: "POST",
    token,
    body: { title, text, lang: "bn" },
  })
}

export async function deleteDocument(id: number, token: string): Promise<void> {
  await apiFetch(`/admin/documents/${id}`, { method: "DELETE", token })
}

export async function uploadDocument(
  file: File,
  title: string,
  token: string
): Promise<DocumentOut> {
  const form = new FormData()
  form.append("file", file)
  form.append("lang", "bn")
  if (title) form.append("title", title)
  const res = await fetch(API_BASE + "/admin/documents/upload", {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
    body: form,
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || "আপলোড ব্যর্থ হয়েছে")
  }
  return res.json()
}

// --- session persistence ---
const SESSION_KEY = "brag"

export function loadSession(): Session | null {
  const raw = safeGet(SESSION_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw)
    if (parsed?.token && parsed?.user) return parsed as Session
  } catch {
    /* ignore */
  }
  return null
}

export function saveSession(session: Session) {
  safeSet(SESSION_KEY, JSON.stringify(session))
}

export function clearSession() {
  safeRemove(SESSION_KEY)
}
