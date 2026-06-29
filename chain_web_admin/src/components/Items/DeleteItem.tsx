import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { LoadingButton } from "@/components/ui/loading-button"
import { itemsDeleteItem } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import type { ItemPublic } from "@chain/api-client"

interface Props {
  item: ItemPublic
  open: boolean
  onOpenChange: (b: boolean) => void
}

function DeleteItem({ item, open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      unwrapResult(itemsDeleteItem({ path: { id: item.id } })),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast("删除成功")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>删除 Item</DialogTitle>
          <DialogDescription>
            确定删除 <strong>{item.title}</strong>？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <LoadingButton
            variant="destructive"
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
          >
            删除
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default DeleteItem