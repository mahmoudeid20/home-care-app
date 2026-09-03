"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import clsx from "clsx";
import { ChevronRight } from "lucide-react";
import { listNursesAdmin } from "@/lib/api";
import type { NurseAdmin } from "@/lib/types";
import { Card, EmptyState, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";
import { StatusPill } from "@/components/StatusPill";
import { Avatar } from "@/components/Avatar";

type Filter = "pending" | "approved" | "all";

const FILTERS: { label: string; value: Filter }[] = [
  { label: "Pending verification", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "All nurses", value: "all" },
];

function verificationSummary(n: NurseAdmin): string {
  const flags = [n.identity_verified, n.qualification_verified, n.experience_verified];
  const verifiedCount = flags.filter(Boolean).length;
  return `${verifiedCount}/3 verified`;
}

export default function NursesPage() {
  const [filter, setFilter] = useState<Filter>("pending");
  const [nurses, setNurses] = useState<NurseAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loading flag set before an async fetch is a safe, standard pattern here
    setIsLoading(true);
    const params =
      filter === "pending"
        ? { pending_verification: true }
        : filter === "approved"
          ? { is_approved: true }
          : {};
    listNursesAdmin(params)
      .then(setNurses)
      .catch((e) => setError(e.message ?? "Couldn't load nurses."))
      .finally(() => setIsLoading(false));
  }, [filter]);

  return (
    <div>
      <PageHeader
        title="Nurse verification"
        description="Review documents and approve nurses before they can accept requests."
      />

      <div className="mb-4 flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={clsx(
              "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
              filter === f.value
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

      {!isLoading && nurses.length === 0 && (
        <EmptyState
          title="No nurses here"
          description="Nobody matches this filter right now — check back once new nurses register."
        />
      )}

      {!isLoading && nurses.length > 0 && (
        <Card>
          <ul>
            {nurses.map((n) => (
              <li key={n.id} className="border-b border-border last:border-0">
                <Link
                  href={`/nurses/${n.id}`}
                  className="flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <Avatar name={n.full_name} photoUrl={n.photo_url} size={40} />
                    <div>
                      <p className="font-medium text-text">{n.full_name}</p>
                      <p className="text-sm text-text-muted">
                        {n.professional_title || "Nurse"} · {n.experience_years} yrs experience
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusPill
                      label={verificationSummary(n)}
                      tone={
                        n.identity_verified && n.qualification_verified && n.experience_verified
                          ? "success"
                          : "warning"
                      }
                    />
                    <StatusPill
                      label={n.is_suspended ? "Suspended" : n.is_approved ? "Approved" : "Not approved"}
                      tone={n.is_suspended ? "danger" : n.is_approved ? "success" : "neutral"}
                    />
                    <ChevronRight size={18} className="text-text-muted" />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
