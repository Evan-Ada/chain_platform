const STORAGE_KEY = "remembered_login_credentials"

type RememberedCredentials = {
  username: string
  password: string
}

function encodePassword(password: string): string {
  return btoa(unescape(encodeURIComponent(password)))
}

function decodePassword(encoded: string): string {
  return decodeURIComponent(escape(atob(encoded)))
}

export function getRememberedCredentials(): RememberedCredentials | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null

    const parsed = JSON.parse(raw) as { username?: string; password?: string }
    if (!parsed.username || !parsed.password) return null

    return {
      username: parsed.username,
      password: decodePassword(parsed.password),
    }
  } catch {
    return null
  }
}

export function saveRememberedCredentials(
  username: string,
  password: string,
): void {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      username,
      password: encodePassword(password),
    }),
  )
}

export function clearRememberedCredentials(): void {
  localStorage.removeItem(STORAGE_KEY)
}
