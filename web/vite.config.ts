import { fileURLToPath, URL } from "node:url"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// base: "./" -> relative asset URLs so the same build works whether it is served at
// "/" (FastAPI / the HF Space) or under a subpath (GitHub Pages: /<repo>/).
// outDir: "../frontend" -> the bundle lands in the directory every deploy target
// already serves, so no Dockerfile / Pages / FastAPI wiring has to change.
export default defineConfig({
  base: "./",
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  build: {
    outDir: "../frontend",
    emptyOutDir: true,
  },
})
