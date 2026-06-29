import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  return (
    <div className="mt-4 max-w-md rounded-lg border border-destructive/50 p-4">
      <h3 className="font-semibold text-destructive">删除账号</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        永久删除你的账号及所有关联数据，此操作不可撤销。
      </p>
      <DeleteConfirmation />
    </div>
  )
}

export default DeleteAccount
