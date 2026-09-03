"use client";

import { FormEvent, useEffect, useState } from "react";
import clsx from "clsx";
import { listPayments, markPaymentPaid } from "@/lib/api";
import type { Payment, PaymentStatus } from "@/lib/types";
import { Card, EmptyState, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";
import { PaymentStatusPill } from "@/components/StatusPill";
import { Button } from "@/components/Button";

const EGP = new Intl.NumberFormat("en-EG", { style: "currency", currency: "EGP" });

const FILTERS: { label: string; value: PaymentStatus | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Pending", value: "PENDING" },
  { label: "Paid", value: "PAID" },
];

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [statusFilter, setStatusFilter] = useState<PaymentStatus | undefined>("PENDING");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markingId, setMarkingId] = useState<string | null>(null);
  const [methodDraft, setMethodDraft] = useState<Record<string, string>>({});

  const load = () => {
    setIsLoading(true);
    listPayments(statusFilter)
      .then(setPayments)
      .catch((e) => setError(e.message ?? "Couldn't load payments."))
      .finally(() => setIsLoading(false));
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect -- loading flag set before an async fetch is a safe, standard pattern here
  useEffect(load, [statusFilter]);

  const handleMarkPaid = async (e: FormEvent, paymentId: string) => {
    e.preventDefault();
    setMarkingId(paymentId);
    setError(null);
    try {
      await markPaymentPaid(paymentId, methodDraft[paymentId] || "cash");
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Couldn't mark this payment as paid.");
    } finally {
      setMarkingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Payments"
        description="Payments are created automatically once a booking completes."
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

      {!isLoading && payments.length === 0 && (
        <EmptyState title="No payments" description="Nothing matches this filter yet." />
      )}

      {!isLoading && payments.length > 0 && (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-muted">
                <th className="px-5 py-3 font-medium">Booking</th>
                <th className="px-5 py-3 font-medium">Amount</th>
                <th className="px-5 py-3 font-medium">Commission</th>
                <th className="px-5 py-3 font-medium">Nurse earnings</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id} className="border-b border-border last:border-0 align-top">
                  <td className="font-mono-ui px-5 py-3 text-xs text-text-muted">
                    {p.booking_id.slice(0, 8)}…
                  </td>
                  <td className="font-mono-ui px-5 py-3 text-text">{EGP.format(p.amount)}</td>
                  <td className="font-mono-ui px-5 py-3 text-text-muted">
                    {EGP.format(p.platform_commission)}
                  </td>
                  <td className="font-mono-ui px-5 py-3 text-text-muted">
                    {EGP.format(p.nurse_earnings)}
                  </td>
                  <td className="px-5 py-3">
                    <PaymentStatusPill status={p.status} />
                  </td>
                  <td className="px-5 py-3 text-right">
                    {p.status === "PENDING" && (
                      <form onSubmit={(e) => handleMarkPaid(e, p.id)} className="flex justify-end gap-2">
                        <select
                          value={methodDraft[p.id] || "cash"}
                          onChange={(e) =>
                            setMethodDraft((prev) => ({ ...prev, [p.id]: e.target.value }))
                          }
                          className="rounded-lg border border-border bg-white px-2 py-1 text-xs"
                        >
                          <option value="cash">Cash</option>
                          <option value="bank_transfer">Bank transfer</option>
                        </select>
                        <Button type="submit" isLoading={markingId === p.id} className="text-xs">
                          Mark paid
                        </Button>
                      </form>
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
