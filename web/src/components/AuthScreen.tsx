import * as React from "react"
import { KeyRound, Loader2, Mail, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ThemeToggle } from "@/components/theme-toggle"
import { login, me, register, saveSession } from "@/lib/api"
import type { Session } from "@/types"

type Mode = "login" | "register"

export function AuthScreen({
  onAuthenticated,
  theme,
  toggleTheme,
}: {
  onAuthenticated: (session: Session) => void
  theme: "light" | "dark"
  toggleTheme: () => void
}) {
  const [mode, setMode] = React.useState<Mode>("login")
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState("")

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const mail = email.trim()
    if (!mail || !password || busy) return
    setBusy(true)
    setError("")
    try {
      if (mode === "register") {
        await register(mail, password)
      }
      const { access_token: token } = await login(mail, password)
      const user = await me(token)
      const session: Session = { token, user }
      saveSession(session)
      onAuthenticated(session)
    } catch (err) {
      setError(err instanceof Error ? err.message : "কিছু একটা ভুল হয়েছে")
      setBusy(false)
    }
  }

  return (
    <div className="relative flex min-h-dvh items-center justify-center p-4">
      <div className="absolute right-4 top-4">
        <ThemeToggle theme={theme} toggle={toggleTheme} />
      </div>

      <div className="w-full max-w-sm animate-fade-in">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/30">
            <Sparkles className="h-7 w-7" />
          </div>
          <h1 className="font-serif text-3xl font-bold tracking-tight">সেবা সহায়ক</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            সরকারি সেবা সম্পর্কে বাংলায় নির্ভরযোগ্য, সূত্রভিত্তিক উত্তর
          </p>
        </div>

        <Card className="shadow-xl shadow-black/5">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">
              {mode === "login" ? "লগইন করুন" : "নতুন অ্যাকাউন্ট"}
            </CardTitle>
            <CardDescription>
              {mode === "login"
                ? "চালিয়ে যেতে আপনার তথ্য দিন"
                : "শুরু করতে একটি অ্যাকাউন্ট তৈরি করুন"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">ইমেইল</Label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    className="pl-9"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={busy}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">পাসওয়ার্ড</Label>
                <div className="relative">
                  <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    placeholder="••••••••"
                    className="pl-9"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={busy}
                  />
                </div>
              </div>

              {error && (
                <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </p>
              )}

              <Button type="submit" className="w-full" disabled={busy}>
                {busy && <Loader2 className="animate-spin" />}
                {mode === "login" ? "লগইন" : "নিবন্ধন করুন"}
              </Button>
            </form>

            <div className="mt-4 text-center text-sm text-muted-foreground">
              {mode === "login" ? "অ্যাকাউন্ট নেই?" : "ইতিমধ্যে অ্যাকাউন্ট আছে?"}{" "}
              <button
                type="button"
                className="font-medium text-primary underline-offset-4 hover:underline disabled:opacity-50"
                disabled={busy}
                onClick={() => {
                  setMode((m) => (m === "login" ? "register" : "login"))
                  setError("")
                }}
              >
                {mode === "login" ? "নিবন্ধন করুন" : "লগইন করুন"}
              </button>
            </div>
          </CardContent>
        </Card>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          BanglaRAG · বাংলা ভাষায় নির্ভরযোগ্য তথ্যসেবা
        </p>
      </div>
    </div>
  )
}
