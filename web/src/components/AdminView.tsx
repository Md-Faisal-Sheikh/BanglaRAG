import * as React from "react"
import { FileText, Loader2, Plus, Trash2, Upload, Type } from "lucide-react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { addDocument, deleteDocument, listDocuments, uploadDocument } from "@/lib/api"
import type { DocumentOut } from "@/types"

export function AdminView({ token }: { token: string }) {
  const [docs, setDocs] = React.useState<DocumentOut[]>([])
  const [loading, setLoading] = React.useState(true)
  const [busy, setBusy] = React.useState(false)
  const [tab, setTab] = React.useState<"text" | "file">("text")
  const [title, setTitle] = React.useState("")
  const [text, setText] = React.useState("")
  const [file, setFile] = React.useState<File | null>(null)
  const fileRef = React.useRef<HTMLInputElement>(null)

  const refresh = React.useCallback(async () => {
    try {
      setDocs(await listDocuments(token))
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "ডকুমেন্ট লোড করা যায়নি")
    } finally {
      setLoading(false)
    }
  }, [token])

  React.useEffect(() => {
    refresh()
  }, [refresh])

  async function submitText() {
    if (!title.trim() || !text.trim() || busy) return
    setBusy(true)
    try {
      await addDocument(title.trim(), text.trim(), token)
      toast.success("ডকুমেন্ট ইনডেক্সে যুক্ত হয়েছে")
      setTitle("")
      setText("")
      await refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "যুক্ত করা যায়নি")
    } finally {
      setBusy(false)
    }
  }

  async function submitFile() {
    if (!file || busy) return
    setBusy(true)
    try {
      const doc = await uploadDocument(file, title.trim(), token)
      toast.success(`"${doc.title}" আপলোড হয়েছে (${doc.n_chunks} অংশ)`)
      setTitle("")
      setFile(null)
      if (fileRef.current) fileRef.current.value = ""
      await refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "আপলোড ব্যর্থ হয়েছে")
    } finally {
      setBusy(false)
    }
  }

  async function remove(doc: DocumentOut) {
    try {
      if (!window.confirm(`"${doc.title}" মুছে ফেলবেন?`)) return
    } catch {
      /* sandboxed iframe: skip confirmation */
    }
    setBusy(true)
    try {
      await deleteDocument(doc.id, token)
      toast.success("ডকুমেন্ট মুছে ফেলা হয়েছে")
      await refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "মুছে ফেলা যায়নি")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6">
      <div className="mb-5">
        <h2 className="font-serif text-2xl font-bold">কর্পাস ব্যবস্থাপনা</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          টেক্সট পেস্ট করুন বা ফাইল আপলোড করুন — উত্তর দেওয়ার জন্য এই নথিগুলোই উৎস।
        </p>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base">নতুন ডকুমেন্ট</CardTitle>
          <div className="flex gap-1 rounded-lg bg-muted p-1">
            <TabButton active={tab === "text"} onClick={() => setTab("text")}>
              <Type className="h-4 w-4" /> টেক্সট
            </TabButton>
            <TabButton active={tab === "file"} onClick={() => setTab("file")}>
              <Upload className="h-4 w-4" /> ফাইল
            </TabButton>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="doc-title">
              শিরোনাম {tab === "file" && <span className="text-muted-foreground">(ঐচ্ছিক)</span>}
            </Label>
            <Input
              id="doc-title"
              placeholder="যেমন: ই-পাসপোর্ট সেবা"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={busy}
            />
          </div>

          {tab === "text" ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="doc-text">বাংলা টেক্সট</Label>
                <Textarea
                  id="doc-text"
                  placeholder="বাংলা টেক্সট এখানে পেস্ট করুন…"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  disabled={busy}
                  className="min-h-[160px]"
                />
              </div>
              <Button onClick={submitText} disabled={busy || !title.trim() || !text.trim()}>
                {busy ? <Loader2 className="animate-spin" /> : <Plus />}
                ইনডেক্সে যুক্ত করুন
              </Button>
            </>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="doc-file">ফাইল</Label>
                <Input
                  id="doc-file"
                  ref={fileRef}
                  type="file"
                  accept=".txt,.md,.pdf,.docx"
                  disabled={busy}
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="cursor-pointer file:mr-3 file:cursor-pointer file:rounded file:text-primary"
                />
                <p className="text-xs text-muted-foreground">
                  সমর্থিত: .txt, .md, .pdf, .docx · সর্বোচ্চ ১০ MB
                </p>
              </div>
              <Button onClick={submitFile} disabled={busy || !file}>
                {busy ? <Loader2 className="animate-spin" /> : <Upload />}
                আপলোড করুন
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <div className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-muted-foreground">
            ইনডেক্সকৃত ডকুমেন্ট {!loading && `(${docs.length})`}
          </h3>
        </div>

        {loading ? (
          <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> লোড হচ্ছে…
          </div>
        ) : docs.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center py-10 text-center text-muted-foreground">
              <FileText className="mb-2 h-8 w-8 opacity-50" />
              <p className="text-sm">এখনো কোনো ডকুমেন্ট যোগ করা হয়নি।</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {docs.map((doc) => (
              <Card key={doc.id} className="transition-colors hover:bg-accent/40">
                <CardContent className="flex items-center justify-between gap-3 p-3.5">
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{doc.title}</p>
                      <div className="mt-0.5 flex items-center gap-1.5">
                        <Badge variant="secondary">সংস্করণ {doc.version}</Badge>
                        <Badge variant="secondary">{doc.n_chunks} অংশ</Badge>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => remove(doc)}
                    disabled={busy}
                    aria-label="মুছুন"
                  >
                    <Trash2 />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "bg-background text-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground"
      )}
    >
      {children}
    </button>
  )
}
