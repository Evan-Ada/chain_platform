import { Link as RouterLink } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface MainProps {
  children?: React.ReactNode
  className?: string
}

export function Main({ children, className }: MainProps) {
  return (
    <main
      className={cn(
        "flex-1 min-w-0 p-4 md:p-6",
        className,
      )}
    >
      {children}
    </main>
  )
}

interface SidebarLinkProps {
  to: string
  icon?: React.ReactNode
  label: string
  active?: boolean
}

export function SidebarLink({ to, icon, label, active }: SidebarLinkProps) {
  return (
    <RouterLink
      to={to}
      className={cn(
        "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
        active && "bg-accent text-accent-foreground",
      )}
    >
      {icon}
      <span>{label}</span>
    </RouterLink>
  )
}

export default Main