import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { LoadingButton } from "@/components/ui/loading-button"
import CronPreview from "@/components/Common/CronPreview"
import {
  scheduledTaskDeleteScheduledTask,
  scheduledTaskUpdateScheduledTask,
} from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import type { ScheduledTaskItem } from "@/types/domain"

const schema = z.object({
  name: z.string().min(1).optional(),
  cron_expr: z.string().min(1).optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  task: ScheduledTaskItem
  open: boolean
  onOpenChange: (b: boolean) => void
}

function EditTask({ task, open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: task.name,
      cron_expr: task.cron_expr,
    },
  })

  useEffect(() => {
    form.reset({ name: task.name, cron_expr: task.cron_expr })
  }, [task, form])

  const cronExpr = form.watch("cron_expr")

  const update = useMutation({
    mutationFn: (data: FormData) =>
      unwrapResult(
        scheduledTaskUpdateScheduledTask({
          body: {
            id: task.id,
            name: data.name,
            cron_expr: data.cron_expr,
          },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-tasks"] })
      showSuccessToast("更新成功")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  const remove = useMutation({
    mutationFn: () =>
      unwrapResult(
        scheduledTaskDeleteScheduledTask({ body: { id: task.id } }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-tasks"] })
      showSuccessToast("已删除")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>编辑任务：{task.name}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((d) => update.mutate(d))}
            className="space-y-3"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名称</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="cron_expr"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>cron</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
                  </FormControl>
                  <CronPreview cronExpr={cronExpr ?? ""} />
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter className="!justify-between">
              <Button
                type="button"
                variant="destructive"
                onClick={() => remove.mutate()}
                disabled={remove.isPending}
              >
                删除
              </Button>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  取消
                </Button>
                <LoadingButton type="submit" loading={update.isPending}>
                  保存
                </LoadingButton>
              </div>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default EditTask