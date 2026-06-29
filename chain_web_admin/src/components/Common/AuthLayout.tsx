import { Link as RouterLink } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface AuthLayoutProps {
  children: React.ReactNode
  title?: string
}

export function AuthLayout({ children, title }: AuthLayoutProps) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="flex flex-col p-6 md:p-10">
        <div className="flex justify-center md:justify-start">
          <RouterLink to="/">
            <span className="text-xl font-semibold tracking-tight">
              链平台
            </span>
          </RouterLink>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm">{children}</div>
        </div>
      </div>
      <div
        className={cn(
          "hidden lg:flex flex-col items-center justify-center bg-muted p-10 text-center",
        )}
      >
        <div className="max-w-md space-y-4">
          <h1 className="text-3xl font-bold tracking-tight">
            {title ?? "智能订阅 · 内容聚合"}
          </h1>
          <p className="text-muted-foreground">
            自定义关键词与来源,自动抓取、AI
            打标、智能推送,把碎片化阅读变得高效。
          </p>
        </div>
      </div>
    </div>
  )
}

export default AuthLayout