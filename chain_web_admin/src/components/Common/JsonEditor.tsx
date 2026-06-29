import { cn } from "@/lib/utils"
import { Textarea } from "@/components/ui/textarea"

interface JsonEditorProps {
  value: string
  onChange: (next: string) => void
  className?: string
  rows?: number
  placeholder?: string
}

export function JsonEditor({
  value,
  onChange,
  className,
  rows = 6,
  placeholder = '{"key": "value"}',
}: JsonEditorProps) {
  return (
    <Textarea
      value={value}
      rows={rows}
      placeholder={placeholder}
      className={cn("font-mono text-xs", className)}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}

export default JsonEditor