import { zodResolver } from "@hookform/resolvers/zod"
import { createFileRoute, Link as RouterLink } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { loginResetPassword } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"

const formSchema = z
  .object({
    token: z.string().min(1, { message: "请输入令牌" }),
    new_password: z.string().min(8, { message: "密码至少8位" }),
    confirm_password: z.string().min(1, { message: "请再次输入密码" }),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "两次密码输入不一致",
    path: ["confirm_password"],
  })

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/reset-password")({
  component: ResetPassword,
})

function ResetPassword() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: {
      token: "",
      new_password: "",
      confirm_password: "",
    },
  })

  const onSubmit = (data: FormData) => {
    const { confirm_password: _cp, ...submitData } = data
    unwrapResult(loginResetPassword({ body: submitData }))
      .then(() => showSuccessToast("密码重置成功,请登录"))
      .catch(handleError.bind(showErrorToast))
  }

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-6"
        >
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="text-2xl font-bold">重置密码</h1>
          </div>

          <FormField
            control={form.control}
            name="token"
            render={({ field }) => (
              <FormItem>
                <FormLabel>令牌</FormLabel>
                <FormControl>
                  <Input
                    data-testid="token-input"
                    placeholder="邮件中的重置令牌"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
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
                  <PasswordInput {...field} />
                </FormControl>
                <FormMessage className="text-xs" />
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
                  <PasswordInput {...field} />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />

          <LoadingButton type="submit" loading={form.formState.isSubmitting}>
            重置密码
          </LoadingButton>

          <div className="text-center text-sm">
            <RouterLink to="/login" className="underline underline-offset-4">
              返回登录
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}

export default ResetPassword