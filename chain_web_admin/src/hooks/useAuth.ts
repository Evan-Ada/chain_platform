import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  type BodyLoginLoginAccessToken,
  type Token,
  type UserPublic,
  type UserRegister,
  type UserUpdateMe,
  loginLoginAccessToken,
  usersReadUserMe,
  usersRegisterUser,
  usersUpdatePasswordMe,
  usersUpdateUserMe,
} from "@chain/api-client"

import { unwrapResult } from "@/lib/unwrap"

const TOKEN_KEY = "access_token"

export const isLoggedIn = () => !!localStorage.getItem(TOKEN_KEY)

export const setAccessToken = (token: string) =>
  localStorage.setItem(TOKEN_KEY, token)

export const clearAccessToken = () => localStorage.removeItem(TOKEN_KEY)

async function loginFn(formData: BodyLoginLoginAccessToken): Promise<Token> {
  const data = await unwrapResult(loginLoginAccessToken({ body: formData }))
  setAccessToken(data.access_token)
  return data
}

async function registerFn(data: UserRegister): Promise<UserPublic> {
  return unwrapResult(usersRegisterUser({ body: data }))
}

async function meFn(): Promise<UserPublic> {
  return unwrapResult(usersReadUserMe({}))
}

async function updateMeFn(data: UserUpdateMe): Promise<UserPublic> {
  return unwrapResult(usersUpdateUserMe({ body: data }))
}

async function updatePasswordFn(
  current_password: string,
  new_password: string,
): Promise<unknown> {
  return unwrapResult(
    usersUpdatePasswordMe({ body: { current_password, new_password } }),
  )
}

function useAuth() {
  const queryClient = useQueryClient()

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: meFn,
    enabled: isLoggedIn(),
    staleTime: 5 * 60 * 1000,
  })

  const loginMutation = useMutation({
    mutationFn: loginFn,
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: ["me"] })
    },
  })

  const signUpMutation = useMutation({
    mutationFn: registerFn,
  })

  const updateMeMutation = useMutation({
    mutationFn: updateMeFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] })
    },
  })

  const updatePasswordMutation = useMutation({
    mutationFn: ({ current_password, new_password }: { current_password: string; new_password: string }) =>
      updatePasswordFn(current_password, new_password),
  })

  const logout = () => {
    clearAccessToken()
    queryClient.clear()
  }

  return {
    user: meQuery.data,
    isLoading: meQuery.isLoading,
    loginMutation,
    signUpMutation,
    updateMeMutation,
    updatePasswordMutation,
    logout,
  }
}

export default useAuth
export { useAuth }