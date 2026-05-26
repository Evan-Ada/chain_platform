import { useQuery } from "@tanstack/react-query"

import { getHealthStatus } from "@/api/health"

export function ApiVersion() {
  const { data } = useQuery({
    queryKey: ["health-status"],
    queryFn: getHealthStatus,
    retry: 1,
    staleTime: 5 * 60 * 1000,
  })

  return (
    <span className="rounded-full border bg-muted px-3 py-1 text-muted-foreground text-xs">
      API {data?.version ? `v${data.version}` : "版本获取中"}
    </span>
  )
}
