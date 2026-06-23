export interface User {
  id: number
  email: string
  is_admin: boolean
}

export interface Citation {
  marker: number
  source: string
  snippet: string
  score?: number | null
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  citations?: Citation[]
  grounded?: boolean
}

export interface DocumentOut {
  id: number
  source: string
  title: string
  lang: string
  version: number
  n_chunks: number
  created_at: string
}

export interface Session {
  token: string
  user: User
}
