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
import { JsonEditor } from "@/components/Common/JsonEditor"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { LoadingButton } from "@/components/ui/loading-button"
import { dataSourceConfigAddDataSourceConfig } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const schema = z.object({
  name: z.string().min(1, "名称必填"),
  source_type: z.string().min(1, "类型必填"),
  config_json: z.string(),
})

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (b: boolean) => void
  onSuccess?: () => void
}

function AddDataSource({ open, onOpenChange, onSuccess }: Props) {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", source_type: "rss", config_json: "{}" },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      let config: Record<string, unknown> = {}
      try {
        config = JSON.parse(data.config_json || "{}")
      } catch {
        throw new Error("config 必须是合法 JSON")
      }
      return unwrapResult(
        dataSourceConfigAddDataSourceConfig({
          body: {
            name: data.name,
            source_type: data.source_type,
            enabled: true,
            config,
          },
        }),
      )
    },
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
          <DialogTitle>新增数据源</DialogTitle>
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
            <FormField
              control={form.control}
              name="source_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>类型 (rss/api/crawler)</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="config_json"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>config (JSON)</FormLabel>
                  <FormControl>
                    <JsonEditor
                      value={field.value}
                      onChange={field.onChange}
                    />
                  </FormControl>
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

export default AddDataSource