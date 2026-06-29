export function Logo({ className }: { className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-2 font-semibold tracking-tight ${className ?? ""}`}
    >
      <span className="inline-block size-6 rounded-md bg-primary" />
      <span>链平台</span>
    </span>
  )
}

export default Logo