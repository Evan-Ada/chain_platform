import { MoreHorizontal } from "lucide-react"
import * as React from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import EditItem from "@/components/Items/EditItem"
import DeleteItem from "@/components/Items/DeleteItem"
import type { ItemPublic } from "@chain/api-client"

interface Props {
  item: ItemPublic
}

function ItemActionsMenu({ item }: Props) {
  const [editOpen, setEditOpen] = React.useState(false)
  const [deleteOpen, setDeleteOpen] = React.useState(false)

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
          <DropdownMenuItem
            onClick={() => setDeleteOpen(true)}
            className="text-destructive"
          >
            删除
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <EditItem item={item} open={editOpen} onOpenChange={setEditOpen} />
      <DeleteItem
        item={item}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}

export default ItemActionsMenu