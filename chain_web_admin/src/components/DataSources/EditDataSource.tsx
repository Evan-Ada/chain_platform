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
import {
  dataSourceConfigDeleteDataSourceConfig,
  dataSourceConfigUpdateDataSourceConfig,
} from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import type { DataSourceConfigItem } from "@/types/domain"

const schema = z.object({
  name: z.string().min(1).optional(),
  source_type: z.string().optional(),
  config_json: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  config: DataSourceConfigItem
  open: boolean
  onOpenChange: (b: boolean) => void
}

function EditDataSource({ config, open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: config.name,
      source_type: config.source_type,
      config_json: JSON.stringify(config.config ?? {}, null, 2),
    },
  })

  useEffect(() => {
    form.reset({
      name: config.name,
      source_type: config.source_type,
      config_json: JSON.stringify(config.config ?? {}, null, 2),
    })
  }, [config, form])

  const update = useMutation({
    mutationFn: (data: FormData) => {
      const payload: Record<string, unknown> = { id: config.id }
      if (data.name !== undefined) payload.name = data.name
      if (data.source_type !== undefined)
        payload.source_type = data.source_type
      if (data.config_json !== undefined) {
        try {
          payload.config = JSON.parse(data.config_json || "{}")
        } catch {
          throw new Error("config 必须是合法 JSON")
        }
      }
      return unwrapResult(
        dataSourceConfigUpdateDataSourceConfig({ body: payload as any }),
      )
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["data-sources"] })
      showSuccessToast("更新成功")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  const remove = useMutation({
    mutationFn: () =>
      unwrapResult(
        dataSourceConfigDeleteDataSourceConfig({
          body: {
            id: config.id,
            name: config.name,
            source_type: config.source_type,
            enabled: config.enabled,
            config: config.config ?? {},
          },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["data-sources"] })
      showSuccessToast("已删除")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>编辑数据源：{config.name}</DialogTitle>
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
              name="source_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>类型</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
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
                      value={field.value ?? "{}"}
                      onChange={field.onChange}
                    />
                  </FormControl>
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

export default EditDataSource