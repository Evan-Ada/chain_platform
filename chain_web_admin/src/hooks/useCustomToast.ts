import { toast } from "sonner"

interface UseCustomToastReturn {
  showSuccessToast: (message: string) => void
  showErrorToast: (message: string) => void
}

function useCustomToast(): UseCustomToastReturn {
  const showSuccessToast = (message: string) => {
    toast.success(message)
  }

  const showErrorToast = (message: string) => {
    toast.error(message)
  }

  return { showSuccessToast, showErrorToast }
}

export default useCustomToast
