import { useEffect, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { getHealthStatus } from "@/api/health"

export function ApiVersion() {
  const [version, setVersion] = useState<string>("...")

  useEffect(() => {
    let mounted = true
    getHealthStatus()
      .then((s) => {
        if (mounted) setVersion(s.version)
      })
      .catch(() => mounted && setVersion("offline"))
    return () => {
      mounted = false
    }
  }, [])

  return (
    <Badge variant="outline" className="font-mono text-xs">
      API v{version}
    </Badge>
  )
}

export default ApiVersion