import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { type UserUpdateMe, usersUpdateUserMe } from "@chain/api-client"
import { Button } from "@/components/ui/button"
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
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { unwrapResult } from "@/lib/unwrap"
import { cn } from "@/lib/utils"
import { handleError } from "@/utils"

const formSchema = z.object({
  full_name: z.string().max(30).optional(),
  email: z.string().optional().or(z.literal("")),
})

type FormData = z.infer<typeof formSchema>

const UserInformation = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const { user: currentUser } = useAuth()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: {
      full_name: currentUser?.full_name ?? undefined,
      email: currentUser?.email ?? "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: UserUpdateMe) =>
      unwrapResult(usersUpdateUserMe({ body: data })),
    onSuccess: () => {
      showSuccessToast("资料已更新")
      setEditMode(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] })
    },
  })

  const onSubmit = (data: FormData) => {
    const updateData: UserUpdateMe = {}
    if (data.full_name !== currentUser?.full_name) {
      updateData.full_name = data.full_name
    }
    if (data.email !== currentUser?.email) {
      updateData.email = data.email
    }
    mutation.mutate(updateData)
  }

  return (
    <div className="max-w-md">
      <h3 className="py-4 text-lg font-semibold">个人资料</h3>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
        >
          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) =>
              editMode ? (
                <FormItem>
                  <FormLabel>姓名</FormLabel>
                  <FormControl>
                    <Input type="text" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              ) : (
                <FormItem>
                  <FormLabel>姓名</FormLabel>
                  <p
                    className={cn(
                      "max-w-sm truncate py-2",
                      !field.value && "text-muted-foreground",
                    )}
                  >
                    {field.value || "未填写"}
                  </p>
                </FormItem>
              )
            }
          />

          <FormField
            control={form.control}
            name="email"
            render={({ field }) =>
              editMode ? (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              ) : (
                <FormItem>
                  <FormLabel>邮箱</FormLabel>
                  <p className="max-w-sm truncate py-2">
                    {field.value || "未填写"}
                  </p>
                </FormItem>
              )
            }
          />

          <div className="flex gap-3">
            {editMode ? (
              <>
                <LoadingButton
                  type="submit"
                  loading={mutation.isPending}
                  disabled={!form.formState.isDirty}
                >
                  保存
                </LoadingButton>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    form.reset()
                    setEditMode(false)
                  }}
                  disabled={mutation.isPending}
                >
                  取消
                </Button>
              </>
            ) : (
              <Button type="button" onClick={() => setEditMode(true)}>
                编辑
              </Button>
            )}
          </div>
        </form>
      </Form>
    </div>
  )
}

export default UserInformation
