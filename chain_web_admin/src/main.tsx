import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router"

import "./index.css"

// 必须先于任何业务函数 import：在 packages 生成的 client 基础上注入 baseUrl + token 拦截器。
import "@/lib/apiClient"
import { routeTree } from "./routeTree.gen"

import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
  queryCache: new QueryCache({}),
  mutationCache: new MutationCache({}),
})

const router = createRouter({ routeTree })

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

const rootEl = document.getElementById("root")!
ReactDOM.createRoot(rootEl).render(
  <StrictMode>
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)