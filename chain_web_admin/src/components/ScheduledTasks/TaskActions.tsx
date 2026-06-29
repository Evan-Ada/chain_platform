import { MoreHorizontal } from "lucide-react"
import * as React from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import EditTask from "@/components/ScheduledTasks/EditTask"
import type { ScheduledTaskItem } from "@/types/domain"

interface Props {
  task: ScheduledTaskItem
}

function TaskActions({ task }: Props) {
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
          <DropdownMenuItem onClick={() => setEditOpen(true)}>编辑</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <EditTask task={task} open={editOpen} onOpenChange={setEditOpen} />
    </>
  )
}

export default TaskActions