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
import { PasswordInput } from "@/components/ui/password-input"
import { usersCreateUser } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const schema = z.object({
  username: z.string().min(3, "用户名至少3个字符"),
  full_name: z.string().optional(),
  email: z.string().email().optional().or(z.literal("")),
  password: z.string().min(6, "密码至少6位"),
  is_superuser: z.boolean().optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (b: boolean) => void
  currentUserId: number
}

function AddUser({ open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: "",
      full_name: "",
      email: "",
      password: "",
      is_superuser: false,
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: FormData) =>
      unwrapResult(
        usersCreateUser({
          body: {
            username: data.username,
            full_name: data.full_name || null,
            email: data.email || null,
            password: data.password,
            is_active: true,
            is_superuser: data.is_superuser ?? false,
          },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      showSuccessToast("创建用户成功")
      onOpenChange(false)
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
  })

  const onSubmit = (data: FormData) => createMutation.mutate(data)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新增用户</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>用户名</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>姓名</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>密码</FormLabel>
                  <FormControl>
                    <PasswordInput {...field} />
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
              <LoadingButton type="submit" loading={createMutation.isPending}>
                创建
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddUser