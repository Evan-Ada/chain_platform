import { Monitor, Moon, Sun } from "lucide-react"

import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"

const OPTIONS = [
  { value: "light" as const, label: "浅色", icon: Sun },
  { value: "dark" as const, label: "深色", icon: Moon },
  { value: "system" as const, label: "跟随系统", icon: Monitor },
]

export function Appearance() {
  const { theme, setTheme } = useTheme()
  return (
    <div className="flex gap-2">
      {OPTIONS.map((opt) => {
        const Icon = opt.icon
        const active = theme === opt.value
        return (
          <Button
            key={opt.value}
            variant={active ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme(opt.value)}
          >
            <Icon className="size-4" />
            {opt.label}
          </Button>
        )
      })}
    </div>
  )
}

export default Appearance