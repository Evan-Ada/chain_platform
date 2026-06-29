import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { type UpdatePassword, usersUpdatePasswordMe } from "@chain/api-client"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useCustomToast from "@/hooks/useCustomToast"
import { unwrapResult } from "@/lib/unwrap"
import { handleError } from "@/utils"

const formSchema = z
  .object({
    current_password: z.string().min(8, "当前密码至少 8 位"),
    new_password: z.string().min(8, "新密码至少 8 位"),
    confirm_password: z.string().min(1, "请确认新密码"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "两次输入的新密码不一致",
    path: ["confirm_password"],
  })

type FormData = z.infer<typeof formSchema>

const ChangePassword = () => {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: UpdatePassword) =>
      unwrapResult(usersUpdatePasswordMe({ body: data })),
    onSuccess: () => {
      showSuccessToast("密码已更新")
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <div className="max-w-md">
      <h3 className="py-4 text-lg font-semibold">修改密码</h3>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((data) => {
            const { confirm_password: _cp, ...payload } = data
            mutation.mutate(payload)
          })}
          className="flex flex-col gap-4"
        >
          <FormField
            control={form.control}
            name="current_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>当前密码</FormLabel>
                <FormControl>
                  <PasswordInput placeholder="请输入当前密码" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="new_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>新密码</FormLabel>
                <FormControl>
                  <PasswordInput placeholder="请输入新密码" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="confirm_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>确认新密码</FormLabel>
                <FormControl>
                  <PasswordInput placeholder="请再次输入新密码" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <LoadingButton type="submit" loading={mutation.isPending}>
            更新密码
          </LoadingButton>
        </form>
      </Form>
    </div>
  )
}

export default ChangePassword
