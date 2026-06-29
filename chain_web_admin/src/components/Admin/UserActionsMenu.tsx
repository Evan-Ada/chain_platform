import { MoreHorizontal } from "lucide-react"
import * as React from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import EditUser from "@/components/Admin/EditUser"
import DeleteUser from "@/components/Admin/DeleteUser"
import type { UserPublic } from "@chain/api-client"

interface Props {
  user: UserPublic
  currentUserId: number
}

function UserActionsMenu({ user, currentUserId }: Props) {
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
          {user.id !== currentUserId && (
            <DropdownMenuItem
              onClick={() => setDeleteOpen(true)}
              className="text-destructive"
            >
              删除
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <EditUser user={user} open={editOpen} onOpenChange={setEditOpen} />
      <DeleteUser
        user={user}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
      />
    </>
  )
}

export default UserActionsMenu