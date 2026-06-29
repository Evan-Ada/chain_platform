import { Link as RouterLink } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"

export function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-3xl font-bold">404 · 页面不存在</h1>
      <p className="text-muted-foreground">您访问的页面已不存在或被移动。</p>
      <Button asChild>
        <RouterLink to="/">回到首页</RouterLink>
      </Button>
    </div>
  )
}

export default NotFound