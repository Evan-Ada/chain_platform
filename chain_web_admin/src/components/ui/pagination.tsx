import { ChevronLeft, ChevronRight } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface PaginationProps {
  pageNum: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({
  pageNum,
  pageSize,
  total,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  return (
    <div className="flex items-center justify-between gap-2 py-2 text-sm">
      <div className="text-muted-foreground">
        共 {total} 条 · 第 {pageNum} / {totalPages} 页
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.max(1, pageNum - 1))}
          disabled={pageNum <= 1}
        >
          <ChevronLeft className="size-4" /> 上一页
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.min(totalPages, pageNum + 1))}
          disabled={pageNum >= totalPages}
        >
          下一页 <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  )
}

export function cn_pagination(...args: Parameters<typeof cn>) {
  return cn(...args)
}