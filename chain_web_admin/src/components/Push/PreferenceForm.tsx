import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { pushGetPreference, pushUpdatePreference } from "@chain/api-client"
import { unwrapApiData } from "@/lib/unwrap"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { Switch } from "@/components/ui/switch"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  push_time: z.string().optional(),
  daily_digest: z.boolean().optional(),
  importance_filter: z.array(z.string()).optional(),
  channels: z.array(z.string()).optional(),
})

type FormData = z.infer<typeof formSchema>

const IMPORTANCE_OPTIONS = [
  { value: "high", label: "高" },
  { value: "medium", label: "中" },
  { value: "low", label: "低" },
]

const CHANNEL_OPTIONS = [
  { value: "email", label: "邮件" },
  { value: "app", label: "应用内" },
]

type PreferenceData = {
  push_time?: string
  daily_digest?: boolean
  importance_filter?: string[]
  channels?: Record<string, boolean>
}

function channelsToArray(channels?: Record<string, boolean>): string[] {
  if (!channels) return []
  return Object.entries(channels)
    .filter(([, enabled]) => enabled)
    .map(([name]) => name)
}

export function PreferenceForm() {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: pref, isLoading } = useQuery({
    queryKey: ["push-preference"],
    queryFn: () =>
      unwrapApiData<PreferenceData>(pushGetPreference({})),
  })

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      push_time: "08:00:00",
      daily_digest: true,
      importance_filter: ["high", "medium"],
      channels: ["email", "app"],
    },
  })

  useEffect(() => {
    if (!pref) return
    form.reset({
      push_time: pref.push_time ?? "08:00:00",
      daily_digest: pref.daily_digest ?? true,
      importance_filter: pref.importance_filter ?? ["high", "medium"],
      channels: channelsToArray(pref.channels),
    })
  }, [pref, form])

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      unwrapApiData<unknown>(
        pushUpdatePreference({
          body: {
            push_time: data.push_time ?? null,
            daily_digest: data.daily_digest ?? null,
            importance_filter: data.importance_filter?.length
              ? data.importance_filter
              : null,
            channels: data.channels?.length
              ? Object.fromEntries(data.channels.map((c) => [c, true]))
              : null,
          },
        }),
      ),
    onSuccess: () => showSuccessToast("推送偏好已保存"),
    onError: handleError.bind(showErrorToast),
  })

  if (isLoading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((d) => mutation.mutate(d))}
        className="space-y-6"
      >
        <FormField
          control={form.control}
          name="push_time"
          render={({ field }) => (
            <FormItem>
              <FormLabel>推送时间</FormLabel>
              <FormControl>
                <Input type="time" {...field} className="w-40" />
              </FormControl>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="daily_digest"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between">
              <FormLabel>每日摘要</FormLabel>
              <FormControl>
                <Switch
                  checked={!!field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="importance_filter"
          render={() => (
            <FormItem>
              <FormLabel>重要性过滤</FormLabel>
              <div className="mt-2 flex flex-wrap gap-4">
                {IMPORTANCE_OPTIONS.map((opt) => (
                  <div key={opt.value} className="flex items-center gap-2">
                    <Checkbox
                      id={`importance-${opt.value}`}
                      checked={form
                        .watch("importance_filter")
                        ?.includes(opt.value)}
                      onCheckedChange={(checked) => {
                        const current =
                          form.getValues("importance_filter") ?? []
                        if (checked) {
                          form.setValue("importance_filter", [
                            ...current,
                            opt.value,
                          ])
                        } else {
                          form.setValue(
                            "importance_filter",
                            current.filter((v) => v !== opt.value),
                          )
                        }
                      }}
                    />
                    <label
                      htmlFor={`importance-${opt.value}`}
                      className="text-sm font-medium"
                    >
                      {opt.label}
                    </label>
                  </div>
                ))}
              </div>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="channels"
          render={() => (
            <FormItem>
              <FormLabel>推送渠道</FormLabel>
              <div className="mt-2 flex flex-wrap gap-4">
                {CHANNEL_OPTIONS.map((opt) => (
                  <div key={opt.value} className="flex items-center gap-2">
                    <Checkbox
                      id={`channel-${opt.value}`}
                      checked={form.watch("channels")?.includes(opt.value)}
                      onCheckedChange={(checked) => {
                        const current = form.getValues("channels") ?? []
                        if (checked) {
                          form.setValue("channels", [...current, opt.value])
                        } else {
                          form.setValue(
                            "channels",
                            current.filter((v) => v !== opt.value),
                          )
                        }
                      }}
                    />
                    <label
                      htmlFor={`channel-${opt.value}`}
                      className="text-sm font-medium"
                    >
                      {opt.label}
                    </label>
                  </div>
                ))}
              </div>
            </FormItem>
          )}
        />

        <LoadingButton type="submit" loading={mutation.isPending}>
          保存偏好
        </LoadingButton>
      </form>
    </Form>
  )
}
