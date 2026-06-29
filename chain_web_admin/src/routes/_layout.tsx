import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import { AppSidebar } from "@/components/Sidebar/AppSidebar"
import { UserMenu } from "@/components/Sidebar/User"
import { Main } from "@/components/Sidebar/Main"
import { ApiVersion } from "@/components/Common/ApiVersion"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({ to: "/login" })
    }
  },
  component: LayoutShell,
})

function LayoutShell() {
  return (
    <div className="flex min-h-screen w-full bg-background">
      <AppSidebar />
      <div className="flex flex-1 flex-col min-w-0">
        <header className="flex h-14 items-center justify-between border-b bg-background px-4">
          <div className="text-sm text-muted-foreground">
            <ApiVersion />
          </div>
          <UserMenu />
        </header>
        <Main>
          <Outlet />
        </Main>
      </div>
    </div>
  )
}