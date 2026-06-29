// Minimal sidebar primitives. The actual sidebar UI is implemented in
// components/Sidebar/AppSidebar.tsx to keep this file small.
import * as React from "react"

import { cn } from "@/lib/utils"

interface SidebarContextValue {
  isMobile: boolean
  open: boolean
  setOpen: (open: boolean) => void
  openMobile: boolean
  setOpenMobile: (open: boolean) => void
  toggleSidebar: () => void
}

const SidebarContext = React.createContext<SidebarContextValue | null>(null)

export function SidebarProvider({
  defaultOpen = true,
  children,
}: {
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [open, setOpen] = React.useState(defaultOpen)
  const [openMobile, setOpenMobile] = React.useState(false)
  const [isMobile, setIsMobile] = React.useState(false)

  React.useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener("resize", check)
    return () => window.removeEventListener("resize", check)
  }, [])

  const toggleSidebar = React.useCallback(() => {
    if (isMobile) setOpenMobile((o) => !o)
    else setOpen((o) => !o)
  }, [isMobile])

  return (
    <SidebarContext.Provider
      value={{
        isMobile,
        open,
        setOpen,
        openMobile,
        setOpenMobile,
        toggleSidebar,
      }}
    >
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar() {
  const ctx = React.useContext(SidebarContext)
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider")
  return ctx
}

export function SidebarInset({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex-1 flex flex-col min-w-0", className)}>
      {children}
    </div>
  )
}