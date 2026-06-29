import { useEffect } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
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
import { llmConfigUpdateLlmConfig } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import type { LlmConfigItem } from "@/types/domain"

const schema = z.object({
  name: z.string().min(1).optional(),
  api_key: z.string().optional(),
  base_url: z.string().optional(),
  model: z.string().optional(),
  enabled: z.boolean().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  config: LlmConfigItem
  open: boolean
  onOpenChange: (b: boolean) => void
}

function EditLLMConfig({ config, open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: config.name,
      api_key: "",
      base_url: config.base_url,
      model: config.model,
      enabled: config.enabled,
    },
  })

  useEffect(() => {
    form.reset({
      name: config.name,
      api_key: "",
      base_url: config.base_url,
      model: config.model,
      enabled: config.enabled,
    })
  }, [config, form])

  const updateMutation = useMutation({
    mutationFn: (data: FormData) => {
      const payload: Record<string, unknown> = { id: config.id }
      if (data.name !== undefined) payload.name = data.name
      if (data.api_key !== undefined && data.api_key.length > 0)
        payload.api_key = data.api_key
      if (data.base_url !== undefined) payload.base_url = data.base_url
      if (data.model !== undefined) payload.model = data.model
      if (data.enabled !== undefined) payload.enabled = data.enabled
      return unwrapResult(llmConfigUpdateLlmConfig({ body: payload as any }))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm-configs"] })
      showSuccessToast("更新成功")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>编辑 LLM 配置：{config.name}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((d) => updateMutation.mutate(d))}
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
              name="api_key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>API Key (留空保留原值)</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder={config.masked_api_key}
                      {...field}
                      value={field.value ?? ""}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="base_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Base URL</FormLabel>
                    <FormControl>
                      <Input {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="model"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Model</FormLabel>
                    <FormControl>
                      <Input {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <LoadingButton type="submit" loading={updateMutation.isPending}>
                保存
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default EditLLMConfig