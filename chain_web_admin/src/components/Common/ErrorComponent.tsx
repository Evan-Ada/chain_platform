import { Link as RouterLink } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"

interface ErrorComponentProps {
  error?: unknown
  reset?: () => void
}

export function ErrorComponent({ error, reset }: ErrorComponentProps) {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : "未知错误"
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-3xl font-bold text-destructive">出错了</h1>
      <p className="max-w-md text-muted-foreground">{message}</p>
      <div className="flex gap-2">
        {reset && (
          <Button onClick={() => reset()}>重试</Button>
        )}
        <Button asChild variant="outline">
          <RouterLink to="/">回到首页</RouterLink>
        </Button>
      </div>
    </div>
  )
}

export default ErrorComponent