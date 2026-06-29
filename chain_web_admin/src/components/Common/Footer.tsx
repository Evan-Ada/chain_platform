export function Footer() {
  return (
    <footer className="border-t py-4 text-sm text-muted-foreground">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4">
        <span>© {new Date().getFullYear()} 链平台 · Sky Load Workspace</span>
        <span className="text-xs">Powered by FastAPI + React + UniApp</span>
      </div>
    </footer>
  )
}

export default Footer