import * as React from "react"
import { Toaster } from "sonner"

import { AdminView } from "@/components/AdminView"
import { AuthScreen } from "@/components/AuthScreen"
import { ChatView } from "@/components/ChatView"
import { Header } from "@/components/Header"
import { useTheme } from "@/components/theme-toggle"
import { clearSession, loadSession } from "@/lib/api"
import type { ChatMessage, Session } from "@/types"

export default function App() {
  const { theme, toggle } = useTheme()
  const [session, setSession] = React.useState<Session | null>(() => loadSession())
  const [view, setView] = React.useState<"chat" | "admin">("chat")
  const [messages, setMessages] = React.useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = React.useState<number | null>(null)

  function logout() {
    clearSession()
    setSession(null)
    setView("chat")
    setMessages([])
    setConversationId(null)
  }

  return (
    <>
      <Toaster theme={theme} position="top-center" richColors />
      {!session ? (
        <AuthScreen onAuthenticated={setSession} theme={theme} toggleTheme={toggle} />
      ) : (
        <div className="flex min-h-dvh flex-col">
          <Header
            user={session.user}
            view={view}
            onToggleView={() => setView((v) => (v === "chat" ? "admin" : "chat"))}
            onLogout={logout}
            theme={theme}
            toggleTheme={toggle}
          />
          <main className="flex flex-1 flex-col">
            {view === "admin" && session.user.is_admin ? (
              <AdminView token={session.token} />
            ) : (
              <ChatView
                token={session.token}
                messages={messages}
                setMessages={setMessages}
                conversationId={conversationId}
                setConversationId={setConversationId}
              />
            )}
          </main>
        </div>
      )}
    </>
  )
}
