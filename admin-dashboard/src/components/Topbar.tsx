"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export function Topbar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="flex h-16 shrink-0 items-center justify-end gap-4 border-b border-border bg-surface px-6">
      <div className="text-right">
        <p className="text-sm font-medium text-text">{user?.email || "Administrator"}</p>
        <p className="text-xs text-text-muted">Admin</p>
      </div>
      <button
        onClick={handleLogout}
        className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-text-muted transition-colors hover:bg-gray-100 hover:text-text"
      >
        <LogOut size={16} />
        Sign out
      </button>
    </header>
  );
}
