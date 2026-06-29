import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"

import { usersDeleteUserMe } from "@chain/api-client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { unwrapResult } from "@/lib/unwrap"
import { handleError } from "@/utils"

const DeleteConfirmation = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { handleSubmit } = useForm()
  const { logout } = useAuth()

  const mutation = useMutation({
    mutationFn: () => unwrapResult(usersDeleteUserMe({})),
    onSuccess: () => {
      showSuccessToast("账号已删除")
      logout()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.clear()
    },
  })

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive" className="mt-3">
          删除账号
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(() => mutation.mutate())}>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              你的所有账号数据将被<strong>永久删除</strong>。若确认继续，请点击「确认删除」。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <DialogClose asChild>
              <Button variant="outline" disabled={mutation.isPending}>
                取消
              </Button>
            </DialogClose>
            <LoadingButton
              variant="destructive"
              type="submit"
              loading={mutation.isPending}
            >
              确认删除
            </LoadingButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default DeleteConfirmation
