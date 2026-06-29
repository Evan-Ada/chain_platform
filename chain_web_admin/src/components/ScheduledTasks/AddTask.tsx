import { useMutation } from "@tanstack/react-query"
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
import { scheduledTaskAddScheduledTask } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const schema = z.object({
  name: z.string().min(1, "名称必填"),
  biz_type: z.string().min(1, "类型必填"),
  biz_id: z.number().optional(),
  cron_expr: z.string().min(1, "cron 必填"),
  enabled: z.boolean().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (b: boolean) => void
  onSuccess?: () => void
}

function AddTask({ open, onOpenChange, onSuccess }: Props) {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      biz_type: "subscription",
      biz_id: undefined as unknown as number,
      cron_expr: "0 8 * * *",
      enabled: true,
    },
  })
  const cronExpr = form.watch("cron_expr")

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      unwrapResult(
        scheduledTaskAddScheduledTask({
          body: {
            name: data.name,
            biz_type: data.biz_type,
            biz_id: data.biz_id ?? null,
            cron_expr: data.cron_expr,
            enabled: data.enabled ?? true,
          },
        }),
      ),
    onSuccess: () => {
      showSuccessToast("创建成功")
      onSuccess?.()
      onOpenChange(false)
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新增定时任务</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((d) => mutation.mutate(d))}
            className="space-y-3"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名称</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="biz_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>业务类型</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="biz_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>业务 ID (可选)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value === ""
                              ? undefined
                              : Number(e.target.value),
                          )
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="cron_expr"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>cron 表达式</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <CronPreview cronExpr={cronExpr} />
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <LoadingButton type="submit" loading={mutation.isPending}>
                创建
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddTask