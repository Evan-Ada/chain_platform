import { MoreHorizontal } from "lucide-react"
import * as React from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import EditDataSource from "@/components/DataSources/EditDataSource"
import type { DataSourceConfigItem } from "@/types/domain"

interface Props {
  config: DataSourceConfigItem
}

function DataSourceActions({ config }: Props) {
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
      <EditDataSource config={config} open={editOpen} onOpenChange={setEditOpen} />
    </>
  )
}

export default DataSourceActions