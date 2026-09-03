"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, ShieldCheck, ShieldOff } from "lucide-react";
import {
  approveDocument,
  approveNurse,
  getNurse,
  getNurseDocuments,
  reactivateNurse,
  rejectDocument,
  suspendNurse,
} from "@/lib/api";
import type { NurseAdmin, NurseDocument } from "@/lib/types";
import { Card, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";
import { DocumentStatusPill, StatusPill } from "@/components/StatusPill";
import { Avatar } from "@/components/Avatar";
import { Button } from "@/components/Button";

const DOC_TYPE_LABEL: Record<string, string> = {
  NATIONAL_ID: "National ID",
  NURSING_CERTIFICATE: "Nursing certificate",
  GRADUATION_CERTIFICATE: "Graduation certificate",
  EXPERIENCE_CERTIFICATE: "Experience certificate",
  OTHER: "Other document",
};

export default function NurseDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const nurseId = params.id;

  const [nurse, setNurse] = useState<NurseAdmin | null>(null);
  const [documents, setDocuments] = useState<NurseDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actioningDocId, setActioningDocId] = useState<string | null>(null);
  const [nurseActionLoading, setNurseActionLoading] = useState(false);
  const [rejectingDocId, setRejectingDocId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const load = useCallback(() => {
    setIsLoading(true);
    Promise.all([getNurse(nurseId), getNurseDocuments(nurseId)])
      .then(([n, docs]) => {
        setNurse(n);
        setDocuments(docs);
      })
      .catch((e) => setError(e.message ?? "Couldn't load this nurse."))
      .finally(() => setIsLoading(false));
  }, [nurseId]);

  // eslint-disable-next-line react-hooks/set-state-in-effect -- loading flag set before an async fetch is a safe, standard pattern here
  useEffect(load, [load]);

  const handleApproveDoc = async (docId: string) => {
    setActioningDocId(docId);
    setError(null);
    try {
      await approveDocument(nurseId, docId);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Couldn't approve this document.");
    } finally {
      setActioningDocId(null);
    }
  };

  const handleRejectDoc = async (docId: string) => {
    setActioningDocId(docId);
    setError(null);
    try {
      await rejectDocument(nurseId, docId, rejectReason || "Document did not meet requirements");
      setRejectingDocId(null);
      setRejectReason("");
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Couldn't reject this document.");
    } finally {
      setActioningDocId(null);
    }
  };

  const handleApproveNurse = async () => {
    setNurseActionLoading(true);
    setError(null);
    try {
      await approveNurse(nurseId);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Couldn't approve this nurse.");
    } finally {
      setNurseActionLoading(false);
    }
  };

  const handleSuspend = async () => {
    setNurseActionLoading(true);
    setError(null);
    try {
      await suspendNurse(nurseId, "Suspended from admin dashboard");
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Couldn't suspend this nurse.");
    } finally {
      setNurseActionLoading(false);
    }
  };

  const handleReactivate = async () => {
    setNurseActionLoading(true);
    setError(null);
    try {
      await reactivateNurse(nurseId);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Couldn't reactivate this nurse.");
    } finally {
      setNurseActionLoading(false);
    }
  };

  if (isLoading) return <LoadingBlock />;
  if (!nurse) return error ? <ErrorBanner message={error} /> : null;

  const fullyVerified =
    nurse.identity_verified && nurse.qualification_verified && nurse.experience_verified;

  return (
    <div>
      <button
        onClick={() => router.push("/nurses")}
        className="mb-4 flex items-center gap-1.5 text-sm text-text-muted hover:text-text"
      >
        <ArrowLeft size={16} /> Back to nurses
      </button>

      <div className="mb-3">
        <Avatar name={nurse.full_name} photoUrl={nurse.photo_url} size={56} />
      </div>
      <PageHeader
        title={nurse.full_name}
        description={nurse.professional_title || undefined}
        action={
          <div className="flex gap-2">
            {nurse.is_suspended ? (
              <Button variant="secondary" isLoading={nurseActionLoading} onClick={handleReactivate}>
                <ShieldCheck size={16} /> Reactivate
              </Button>
            ) : (
              <Button variant="danger" isLoading={nurseActionLoading} onClick={handleSuspend}>
                <ShieldOff size={16} /> Suspend
              </Button>
            )}
            {!nurse.is_approved && !nurse.is_suspended && (
              <Button isLoading={nurseActionLoading} disabled={!fullyVerified} onClick={handleApproveNurse}>
                Approve nurse
              </Button>
            )}
          </div>
        }
      />

      {error && <ErrorBanner message={error} />}

      <div className="mb-6 flex flex-wrap gap-2">
        <StatusPill
          label={nurse.is_suspended ? "Suspended" : nurse.is_approved ? "Approved" : "Not approved"}
          tone={nurse.is_suspended ? "danger" : nurse.is_approved ? "success" : "neutral"}
        />
        <StatusPill label={`${nurse.experience_years} yrs experience`} tone="neutral" />
        <StatusPill label={`${nurse.average_rating.toFixed(1)}★ (${nurse.review_count})`} tone="neutral" />
      </div>

      {!nurse.is_approved && !fullyVerified && (
        <div className="mb-6 rounded-lg border border-accent/30 bg-accent-soft px-4 py-3 text-sm text-accent">
          This nurse can&apos;t be approved until identity, qualification, and experience documents
          are all approved below.
        </div>
      )}

      <Card className="p-5">
        <h2 className="font-display text-lg font-semibold text-text">Verification documents</h2>
        <p className="mt-1 text-sm text-text-muted">
          Approving a document marks the matching verification flag. Approving the nurse (above)
          is a separate, final step.
        </p>

        {documents.length === 0 ? (
          <p className="mt-4 text-sm text-text-muted">No documents uploaded yet.</p>
        ) : (
          <ul className="mt-4 divide-y divide-border">
            {documents.map((doc) => (
              <li key={doc.id} className="py-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-soft text-primary">
                      <FileText size={16} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text">
                        {DOC_TYPE_LABEL[doc.document_type] ?? doc.document_type}
                      </p>
                      {doc.status === "REJECTED" && doc.rejection_reason && (
                        <p className="text-xs text-danger">{doc.rejection_reason}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <DocumentStatusPill status={doc.status} />
                    {doc.status === "PENDING" && (
                      <div className="flex gap-2">
                        <Button
                          variant="secondary"
                          className="text-xs"
                          isLoading={actioningDocId === doc.id}
                          onClick={() => handleApproveDoc(doc.id)}
                        >
                          Approve
                        </Button>
                        <Button
                          variant="danger"
                          className="text-xs"
                          onClick={() => setRejectingDocId(doc.id)}
                        >
                          Reject
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                {rejectingDocId === doc.id && (
                  <div className="mt-3 flex gap-2 rounded-lg bg-gray-50 p-3">
                    <input
                      autoFocus
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      placeholder="Reason for rejection (shown to the nurse)"
                      className="flex-1 rounded-lg border border-border bg-white px-3 py-1.5 text-sm"
                    />
                    <Button
                      variant="danger"
                      className="text-xs"
                      isLoading={actioningDocId === doc.id}
                      onClick={() => handleRejectDoc(doc.id)}
                    >
                      Confirm reject
                    </Button>
                    <Button
                      variant="ghost"
                      className="text-xs"
                      onClick={() => {
                        setRejectingDocId(null);
                        setRejectReason("");
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
