"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  LayoutDashboard,
  Users,
  BadgeCheck,
  ClipboardList,
  Wallet,
  MessageSquareWarning,
  Settings,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/users", label: "Users", icon: Users },
  { href: "/nurses", label: "Nurse verification", icon: BadgeCheck },
  { href: "/catalog", label: "Services & specialties", icon: ClipboardList },
  { href: "/payments", label: "Payments", icon: Wallet },
  { href: "/complaints", label: "Complaints", icon: MessageSquareWarning },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col bg-primary-dark text-white">
      <div className="px-6 py-6">
        <p className="font-display text-xl font-semibold italic">HomeCare</p>
        <p className="text-xs uppercase tracking-wider text-white/60">Admin</p>
      </div>
      <nav className="flex-1 space-y-0.5 px-3">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-white/10 font-medium text-white"
                  : "text-white/70 hover:bg-white/5 hover:text-white"
              )}
            >
              <Icon size={18} strokeWidth={2} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-6 py-4 text-xs text-white/40">Platform administration</div>
    </aside>
  );
}
