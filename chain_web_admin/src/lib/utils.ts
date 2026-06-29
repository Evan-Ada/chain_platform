import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const getBaseUrl = (): string => {
  const raw = (import.meta.env.VITE_API_URL as string | undefined) || ""
  return raw.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "")
}