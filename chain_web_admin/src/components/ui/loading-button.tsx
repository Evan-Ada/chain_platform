import { Loader2 } from "lucide-react"

import { Button, type ButtonProps } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface LoadingButtonProps extends ButtonProps {
  loading?: boolean
}

const LoadingButton = ({
  loading = false,
  disabled,
  className,
  children,
  ...props
}: LoadingButtonProps) => {
  return (
    <Button
      disabled={loading || disabled}
      className={cn("flex items-center gap-2", className)}
      {...props}
    >
      {loading && <Loader2 className="size-4 animate-spin" />}
      {children}
    </Button>
  )
}

export { LoadingButton }