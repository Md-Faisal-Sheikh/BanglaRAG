import * as React from "react"
import { Moon, Sun } from "lucide-react"

import { Button } from "@/components/ui/button"

const STORAGE_KEY = "brag-theme"

function getInitial(): "light" | "dark" {
  if (typeof document !== "undefined" && document.documentElement.classList.contains("dark")) {
    return "dark"
  }
  return "light"
}

export function useTheme() {
  const [theme, setTheme] = React.useState<"light" | "dark">(getInitial)

  React.useEffect(() => {
    const root = document.documentElement
    root.classList.toggle("dark", theme === "dark")
    try {
      window.localStorage?.setItem(STORAGE_KEY, theme)
    } catch {
      /* ignore */
    }
  }, [theme])

  const toggle = React.useCallback(
    () => setTheme((t) => (t === "dark" ? "light" : "dark")),
    []
  )
  return { theme, toggle }
}

export function ThemeToggle({ theme, toggle }: { theme: "light" | "dark"; toggle: () => void }) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label={theme === "dark" ? "লাইট মোড" : "ডার্ক মোড"}
      title={theme === "dark" ? "লাইট মোড" : "ডার্ক মোড"}
    >
      {theme === "dark" ? <Sun /> : <Moon />}
    </Button>
  )
}
