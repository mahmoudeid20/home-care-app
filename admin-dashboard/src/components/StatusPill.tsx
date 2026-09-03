import clsx from "clsx";

type Tone = "neutral" | "success" | "warning" | "danger" | "info";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-gray-100 text-gray-700",
  success: "bg-success-soft text-success",
  warning: "bg-accent-soft text-accent",
  danger: "bg-danger-soft text-danger",
  info: "bg-primary-soft text-primary",
};

export function StatusPill({ label, tone = "neutral" }: { label: string; tone?: Tone }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        toneClasses[tone]
      )}
    >
      {label}
    </span>
  );
}

const DOCUMENT_STATUS_TONE: Record<string, Tone> = {
  PENDING: "warning",
  APPROVED: "success",
  REJECTED: "danger",
};

export function DocumentStatusPill({ status }: { status: string }) {
  return <StatusPill label={status} tone={DOCUMENT_STATUS_TONE[status] ?? "neutral"} />;
}

const PAYMENT_STATUS_TONE: Record<string, Tone> = {
  PENDING: "warning",
  PAID: "success",
  FAILED: "danger",
  REFUNDED: "info",
  CANCELLED: "neutral",
};

export function PaymentStatusPill({ status }: { status: string }) {
  return <StatusPill label={status} tone={PAYMENT_STATUS_TONE[status] ?? "neutral"} />;
}

const COMPLAINT_STATUS_TONE: Record<string, Tone> = {
  OPEN: "warning",
  IN_REVIEW: "info",
  RESOLVED: "success",
  CLOSED: "neutral",
};

export function ComplaintStatusPill({ status }: { status: string }) {
  return (
    <StatusPill label={status.replace("_", " ")} tone={COMPLAINT_STATUS_TONE[status] ?? "neutral"} />
  );
}
