import { LogOut, MessageSquare, Database, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import type { User } from "@/types"

export function Header({
  user,
  view,
  onToggleView,
  onLogout,
  theme,
  toggleTheme,
}: {
  user: User
  view: "chat" | "admin"
  onToggleView: () => void
  onLogout: () => void
  theme: "light" | "dark"
  toggleTheme: () => void
}) {
  return (
    <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 w-full max-w-3xl items-center justify-between gap-3 px-4">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="font-serif text-lg font-bold tracking-tight truncate">সেবা সহায়ক</span>
        </div>

        <nav className="flex items-center gap-1">
          {user.is_admin && (
            <Button variant="ghost" size="sm" className="gap-1.5" onClick={onToggleView}>
              {view === "chat" ? (
                <>
                  <Database className="h-4 w-4" /> কর্পাস
                </>
              ) : (
                <>
                  <MessageSquare className="h-4 w-4" /> চ্যাট
                </>
              )}
            </Button>
          )}
          <span className="hidden max-w-[160px] truncate px-2 text-sm text-muted-foreground sm:inline">
            {user.email}
          </span>
          <ThemeToggle theme={theme} toggle={toggleTheme} />
          <Button variant="ghost" size="icon" onClick={onLogout} aria-label="লগআউট" title="লগআউট">
            <LogOut />
          </Button>
        </nav>
      </div>
    </header>
  )
}
