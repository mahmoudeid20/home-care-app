"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { activateUser, deactivateUser, listUsers } from "@/lib/api";
import type { UserAdmin, UserRole } from "@/lib/types";
import { Card, EmptyState, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";
import { StatusPill } from "@/components/StatusPill";
import { Button } from "@/components/Button";

const ROLE_FILTERS: { label: string; value: UserRole | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Patients", value: "PATIENT" },
  { label: "Nurses", value: "NURSE" },
  { label: "Admins", value: "ADMIN" },
];

export default function UsersPage() {
  const [users, setUsers] = useState<UserAdmin[]>([]);
  const [roleFilter, setRoleFilter] = useState<UserRole | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actioningId, setActioningId] = useState<string | null>(null);

  const load = () => {
    setIsLoading(true);
    listUsers(roleFilter)
      .then(setUsers)
      .catch((e) => setError(e.message ?? "Couldn't load users."))
      .finally(() => setIsLoading(false));
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect -- loading flag set before an async fetch is a safe, standard pattern here
  useEffect(load, [roleFilter]);

  const handleToggleActive = async (user: UserAdmin) => {
    setActioningId(user.id);
    try {
      if (user.is_active) {
        await deactivateUser(user.id, "Deactivated from admin dashboard");
      } else {
        await activateUser(user.id);
      }
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Action failed.");
    } finally {
      setActioningId(null);
    }
  };

  return (
    <div>
      <PageHeader title="Users" description="Everyone with an account on HomeCare." />

      <div className="mb-4 flex gap-2">
        {ROLE_FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => setRoleFilter(f.value)}
            className={clsx(
              "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
              roleFilter === f.value
                ? "bg-primary text-white"
                : "bg-white text-text-muted border border-border hover:text-text"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <ErrorBanner message={error} />}
      {isLoading && <LoadingBlock />}

      {!isLoading && users.length === 0 && (
        <EmptyState title="No users found" description="Nobody matches this filter yet." />
      )}

      {!isLoading && users.length > 0 && (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-muted">
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Role</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Joined</th>
                <th className="px-5 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-border last:border-0">
                  <td className="px-5 py-3 text-text">{u.email}</td>
                  <td className="px-5 py-3 text-text-muted">{u.role}</td>
                  <td className="px-5 py-3">
                    <StatusPill
                      label={u.is_active ? "Active" : "Deactivated"}
                      tone={u.is_active ? "success" : "danger"}
                    />
                  </td>
                  <td className="font-mono-ui px-5 py-3 text-text-muted">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {u.role !== "ADMIN" && (
                      <Button
                        variant={u.is_active ? "danger" : "secondary"}
                        isLoading={actioningId === u.id}
                        onClick={() => handleToggleActive(u)}
                        className="text-xs"
                      >
                        {u.is_active ? "Deactivate" : "Activate"}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
