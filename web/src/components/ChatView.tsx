import * as React from "react"
import { ArrowUp, BadgeCheck, Loader2, Quote, Sparkles, TriangleAlert } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { sendChat } from "@/lib/api"
import type { ChatMessage } from "@/types"

const SUGGESTIONS = [
  "ই-পাসপোর্টের জন্য কোথায় আবেদন করতে হয়?",
  "জাতীয় পরিচয়পত্র সংশোধন কীভাবে করব?",
  "পাসপোর্ট ফি কত এবং কোথায় জমা দিতে হয়?",
]

export function ChatView({
  token,
  messages,
  setMessages,
  conversationId,
  setConversationId,
}: {
  token: string
  messages: ChatMessage[]
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  conversationId: number | null
  setConversationId: (id: number | null) => void
}) {
  const [input, setInput] = React.useState("")
  const [busy, setBusy] = React.useState(false)
  const [openCitation, setOpenCitation] = React.useState<string | null>(null)
  const endRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, busy])

  async function ask(question: string) {
    const q = question.trim()
    if (!q || busy) return
    setInput("")
    setOpenCitation(null)
    setMessages((prev) => [...prev, { role: "user", content: q }])
    setBusy(true)
    try {
      const res = await sendChat(q, conversationId, token)
      setConversationId(res.conversation_id)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.answer,
          citations: res.citations ?? [],
          grounded: res.grounded,
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "ত্রুটি: " + (err instanceof Error ? err.message : "উত্তর আনা যায়নি"),
          grounded: false,
        },
      ])
    } finally {
      setBusy(false)
    }
  }

  const empty = messages.length === 0

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4">
      <div className="flex-1 space-y-5 py-6">
        {empty ? (
          <div className="mt-10 flex flex-col items-center text-center animate-fade-in sm:mt-20">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-accent-foreground">
              <Sparkles className="h-6 w-6" />
            </div>
            <h2 className="font-serif text-2xl font-bold">কীভাবে সাহায্য করতে পারি?</h2>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              সরকারি সেবা সম্পর্কে প্রশ্ন করুন — উত্তর আসবে তথ্যসূত্রসহ, আর সূত্রে না থাকলে
              অনুমান না করে জানিয়ে দেওয়া হবে।
            </p>
            <div className="mt-6 grid w-full max-w-md gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => ask(s)}
                  className="rounded-lg border bg-card px-4 py-3 text-left text-sm text-card-foreground shadow-sm transition-colors hover:border-primary/40 hover:bg-accent"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <MessageBubble
              key={i}
              message={m}
              index={i}
              openCitation={openCitation}
              onToggleCitation={(key) =>
                setOpenCitation((cur) => (cur === key ? null : key))
              }
            />
          ))
        )}

        {busy && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground animate-fade-in">
            <Loader2 className="h-4 w-4 animate-spin" />
            উত্তর তৈরি হচ্ছে…
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-0 -mx-4 bg-gradient-to-t from-background via-background to-transparent px-4 pb-5 pt-3">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            ask(input)
          }}
          className="mx-auto flex max-w-3xl items-center gap-2 rounded-2xl border bg-card p-1.5 shadow-lg shadow-black/5 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-ring/30"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="আপনার প্রশ্ন লিখুন…"
            disabled={busy}
            className="border-0 bg-transparent shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
          />
          <Button type="submit" size="icon" className="h-9 w-9 shrink-0 rounded-xl" disabled={busy || !input.trim()}>
            {busy ? <Loader2 className="animate-spin" /> : <ArrowUp />}
          </Button>
        </form>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          উত্তর তথ্যসূত্রভিত্তিক; যাচাই করে নিন।
        </p>
      </div>
    </div>
  )
}

function MessageBubble({
  message,
  index,
  openCitation,
  onToggleCitation,
}: {
  message: ChatMessage
  index: number
  openCitation: string | null
  onToggleCitation: (key: string) => void
}) {
  const isUser = message.role === "user"
  const citations = message.citations ?? []
  const openItem = citations.find((c) => openCitation === `${index}-${c.marker}`)

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm leading-relaxed text-primary-foreground shadow-sm">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start animate-fade-in">
      <div className="max-w-[88%] space-y-2.5">
        <div className="whitespace-pre-wrap rounded-2xl rounded-bl-md border bg-card px-4 py-3 text-sm leading-relaxed text-card-foreground shadow-sm">
          {message.content}
        </div>

        <div className="flex flex-wrap items-center gap-2 px-1">
          {message.grounded === false ? (
            <Badge variant="warning">
              <TriangleAlert className="h-3 w-3" /> তথ্যসূত্রে উত্তর পাওয়া যায়নি
            </Badge>
          ) : (
            <Badge variant="success">
              <BadgeCheck className="h-3 w-3" /> সূত্রভিত্তিক উত্তর
            </Badge>
          )}
          {citations.map((c) => {
            const key = `${index}-${c.marker}`
            return (
              <button
                key={key}
                onClick={() => onToggleCitation(key)}
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors hover:bg-accent",
                  openCitation === key
                    ? "border-primary/50 bg-accent text-accent-foreground"
                    : "text-muted-foreground"
                )}
              >
                <Quote className="h-3 w-3" /> সূত্র [{c.marker}] · {c.source}
              </button>
            )
          })}
        </div>

        {openItem && (
          <div className="rounded-lg border bg-muted/50 px-3.5 py-3 text-sm leading-relaxed text-foreground/90 animate-fade-in">
            {openItem.snippet}…
          </div>
        )}
      </div>
    </div>
  )
}
