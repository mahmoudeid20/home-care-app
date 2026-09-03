"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { listComplaintsAdmin, updateComplaintAdmin } from "@/lib/api";
import type { Complaint, ComplaintStatus } from "@/lib/types";
import { Card, EmptyState, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";
import { ComplaintStatusPill } from "@/components/StatusPill";
import { Button } from "@/components/Button";

const FILTERS: { label: string; value: ComplaintStatus | undefined }[] = [
  { label: "Open", value: "OPEN" },
  { label: "In review", value: "IN_REVIEW" },
  { label: "Resolved", value: "RESOLVED" },
  { label: "All", value: undefined },
];

export default function ComplaintsPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [statusFilter, setStatusFilter] = useState<ComplaintStatus | undefined>("OPEN");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [responseDraft, setResponseDraft] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);

  const load = () => {
    setIsLoading(true);
    listComplaintsAdmin(statusFilter)
      .then(setComplaints)
      .catch((e) => setError(e.message ?? "Couldn't load complaints."))
      .finally(() => setIsLoading(false));
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect -- loading flag set before an async fetch is a safe, standard pattern here
  useEffect(load, [statusFilter]);

  const handleUpdate = async (id: string, status: ComplaintStatus) => {
    setSavingId(id);
    setError(null);
    try {
      await updateComplaintAdmin(id, status, responseDraft[id]);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Couldn't update this complaint.");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Complaints"
        description="Filed by patients or nurses; triage and respond here."
      />

      <div className="mb-4 flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => setStatusFilter(f.value)}
            className={clsx(
              "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
              statusFilter === f.value
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

      {!isLoading && complaints.length === 0 && (
        <EmptyState title="Nothing here" description="No complaints match this filter." />
      )}

      {!isLoading && complaints.length > 0 && (
        <Card>
          <ul className="divide-y divide-border">
            {complaints.map((c) => (
              <li key={c.id} className="p-5">
                <button
                  className="flex w-full items-start justify-between gap-4 text-left"
                  onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}
                >
                  <div>
                    <p className="text-sm font-medium capitalize text-text">
                      {c.category.replace(/_/g, " ")}
                    </p>
                    <p className="mt-1 line-clamp-2 text-sm text-text-muted">{c.description}</p>
                  </div>
                  <ComplaintStatusPill status={c.status} />
                </button>

                {expandedId === c.id && (
                  <div className="mt-4 space-y-3 rounded-lg bg-gray-50 p-4">
                    <p className="text-sm text-text">{c.description}</p>
                    {c.admin_response && (
                      <p className="rounded-lg bg-primary-soft px-3 py-2 text-sm text-primary">
                        Previous response: {c.admin_response}
                      </p>
                    )}
                    <textarea
                      value={responseDraft[c.id] ?? c.admin_response ?? ""}
                      onChange={(e) =>
                        setResponseDraft((prev) => ({ ...prev, [c.id]: e.target.value }))
                      }
                      placeholder="Write a response…"
                      rows={2}
                      className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm"
                    />
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        className="text-xs"
                        isLoading={savingId === c.id}
                        onClick={() => handleUpdate(c.id, "IN_REVIEW")}
                      >
                        Mark in review
                      </Button>
                      <Button
                        className="text-xs"
                        isLoading={savingId === c.id}
                        onClick={() => handleUpdate(c.id, "RESOLVED")}
                      >
                        Resolve
                      </Button>
                      <Button
                        variant="ghost"
                        className="text-xs"
                        isLoading={savingId === c.id}
                        onClick={() => handleUpdate(c.id, "CLOSED")}
                      >
                        Close
                      </Button>
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
