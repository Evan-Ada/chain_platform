import * as React from "react"

const Collapsible = ({ children }: { children: React.ReactNode }) => (
  <div>{children}</div>
)
const CollapsibleTrigger = ({ children }: { children: React.ReactNode }) => (
  <>{children}</>
)
const CollapsibleContent = ({ children }: { children: React.ReactNode }) => (
  <div>{children}</div>
)

export { Collapsible, CollapsibleTrigger, CollapsibleContent }
