import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useEffect } from "react"

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
import { usersUpdateUser } from "@chain/api-client"
import { unwrapResult } from "@/lib/unwrap"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import type { UserPublic } from "@chain/api-client"

const schema = z.object({
  email: z.string().email().optional().or(z.literal("")),
  full_name: z.string().optional(),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
})

type FormData = z.infer<typeof schema>

interface Props {
  user: UserPublic
  open: boolean
  onOpenChange: (b: boolean) => void
}

function EditUser({ user, open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: user.email ?? "",
      full_name: user.full_name ?? "",
      is_active: user.is_active,
      is_superuser: user.is_superuser,
    },
  })

  useEffect(() => {
    form.reset({
      email: user.email ?? "",
      full_name: user.full_name ?? "",
      is_active: user.is_active,
      is_superuser: user.is_superuser,
    })
  }, [user, form])

  const updateMutation = useMutation({
    mutationFn: (data: FormData) =>
      unwrapResult(
        usersUpdateUser({
          path: { user_id: user.id },
          body: {
            email: data.email || null,
            full_name: data.full_name || null,
            is_active: data.is_active,
            is_superuser: data.is_superuser,
          },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      showSuccessToast("更新成功")
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>编辑用户：{user.username}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((d) => updateMutation.mutate(d))}
            className="space-y-3"
          >
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

export default EditUser