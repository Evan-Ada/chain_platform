import {
  Bell,
  Calendar,
  Database,
  Home,
  KeyRound,
  Lightbulb,
  ListChecks,
  Settings,
  Tag,
  Users,
} from "lucide-react"

import { useAuth } from "@/hooks/useAuth"
import { SidebarLink } from "./Main"
import { Logo } from "@/components/Common/Logo"

export function AppSidebar() {
  const { user } = useAuth()
  const isSuperuser = !!user?.is_superuser

  return (
    <aside className="hidden md:flex md:w-56 md:flex-col md:border-r md:bg-muted/30">
      <div className="flex h-14 items-center px-4 border-b">
        <Logo />
      </div>
      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        <SidebarLink to="/" icon={<Home className="size-4" />} label="仪表盘" />
        <SidebarLink
          to="/subscriptions"
          icon={<Bell className="size-4" />}
          label="订阅"
        />
        <SidebarLink
          to="/data-sources"
          icon={<Database className="size-4" />}
          label="数据源"
        />
        <SidebarLink
          to="/scheduled-tasks"
          icon={<Calendar className="size-4" />}
          label="定时任务"
        />
        <SidebarLink
          to="/llm-config"
          icon={<KeyRound className="size-4" />}
          label="LLM 配置"
        />
        {isSuperuser && (
          <SidebarLink
            to="/admin"
            icon={<Users className="size-4" />}
            label="用户管理"
          />
        )}
        <SidebarLink
          to="/items"
          icon={<ListChecks className="size-4" />}
          label="Items"
        />
        <SidebarLink
          to="/insights"
          icon={<Lightbulb className="size-4" />}
          label="洞见"
        />
        <SidebarLink
          to="/tags"
          icon={<Tag className="size-4" />}
          label="标签管理"
        />
        <SidebarLink
          to="/settings"
          icon={<Settings className="size-4" />}
          label="设置"
        />
      </nav>
    </aside>
  )
}

export default AppSidebar