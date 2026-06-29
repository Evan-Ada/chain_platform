import { useMutation, useQuery } from "@tanstack/react-query"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  llmConfigAddLlmConfig,
  llmConfigListProviders,
  llmConfigTestLlmConfig,
} from "@chain/api-client"
import { unwrapApiData, unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const schema = z.object({
  name: z.string().min(1, "名称必填"),
  provider: z.string().min(1, "Provider 必填"),
  api_key: z.string().min(1, "API Key 必填"),
  base_url: z.string(),
  model: z.string(),
})

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (b: boolean) => void
  onSuccess?: () => void
}

function AddLLMConfig({ open, onOpenChange, onSuccess }: Props) {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      provider: "openai",
      api_key: "",
      base_url: "https://api.openai.com/v1",
      model: "gpt-4o-mini",
    },
  })

  const { data: providers } = useQuery({
    queryKey: ["llm-providers"],
    queryFn: () =>
      unwrapApiData<Array<{ id: string; name: string }>>(
        llmConfigListProviders({}),
      ),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })

  const addMutation = useMutation({
    mutationFn: (data: FormData) =>
      unwrapResult(
        llmConfigAddLlmConfig({
          body: {
            name: data.name,
            provider: data.provider,
            api_key: data.api_key,
            base_url: data.base_url,
            model: data.model,
            enabled: true,
            is_default: false,
            extra: {},
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

  const testMutation = useMutation({
    mutationFn: (data: FormData) =>
      unwrapApiData<{ reply: string; latency_ms: number }>(
        llmConfigTestLlmConfig({
          body: {
            api_key: data.api_key,
            base_url: data.base_url,
            model: data.model,
            provider: data.provider,
          },
        }),
      ),
    onSuccess: (res) =>
      showSuccessToast(`测试成功: ${res.reply} (${res.latency_ms}ms)`),
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新增 LLM 配置</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((d) => addMutation.mutate(d))}
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
              name="provider"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Provider</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择 Provider" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {(providers ?? []).map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="api_key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>API Key</FormLabel>
                  <FormControl>
                    <Input type="password" {...field} />
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
            <DialogFooter className="!justify-between">
              <LoadingButton
                type="button"
                variant="outline"
                onClick={() => testMutation.mutate(form.getValues())}
                loading={testMutation.isPending}
              >
                测试连通性
              </LoadingButton>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  取消
                </Button>
                <LoadingButton
                  type="submit"
                  loading={addMutation.isPending}
                >
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

export default AddLLMConfig