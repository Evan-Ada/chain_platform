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
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { loginRecoverPassword } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"

const formSchema = z.object({
  email: z.string().email({ message: "邮箱格式不正确" }),
})

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/recover-password")({
  component: RecoverPassword,
})

function RecoverPassword() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: { email: "" },
  })

  const onSubmit = (data: FormData) => {
    unwrapResult(
      loginRecoverPassword({ path: { email: data.email } }),
    )
      .then(() =>
        showSuccessToast("如果该邮箱已注册,您将收到密码重置链接"),
      )
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
            <h1 className="text-2xl font-bold">找回密码</h1>
            <p className="text-sm text-muted-foreground">
              输入注册邮箱,我们将发送重置链接。
            </p>
          </div>

          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>邮箱</FormLabel>
                <FormControl>
                  <Input
                    data-testid="email-input"
                    placeholder="you@example.com"
                    type="email"
                    {...field}
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />

          <LoadingButton type="submit" loading={form.formState.isSubmitting}>
            发送重置链接
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

export default RecoverPassword