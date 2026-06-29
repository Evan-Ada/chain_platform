import { MoreHorizontal } from "lucide-react"
import * as React from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import EditSubscription from "@/components/Subscriptions/EditSubscription"
import type { SubscriptionItem } from "@/types/domain"

interface Props {
  subscription: SubscriptionItem
}

function SubscriptionActions({ subscription }: Props) {
  const [editOpen, setEditOpen] = React.useState(false)
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="size-8">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => setEditOpen(true)}>
            编辑
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <EditSubscription
        subscription={subscription}
        open={editOpen}
        onOpenChange={setEditOpen}
      />
    </>
  )
}

export default SubscriptionActions