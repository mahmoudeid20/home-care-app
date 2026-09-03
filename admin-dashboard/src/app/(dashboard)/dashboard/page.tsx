"use client";

import { useEffect, useState } from "react";
import {
  Users,
  BadgeCheck,
  Clock,
  Activity,
  CheckCircle2,
  XCircle,
  Wallet,
  Percent,
  Star,
} from "lucide-react";
import { getStats } from "@/lib/api";
import type { PlatformStats } from "@/lib/types";
import { Card, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";

const EGP = new Intl.NumberFormat("en-EG", {
  style: "currency",
  currency: "EGP",
  maximumFractionDigits: 0,
});

function StatCard({
  icon: Icon,
  label,
  value,
  tone = "default",
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  tone?: "default" | "accent" | "danger";
}) {
  const iconBg =
    tone === "accent"
      ? "bg-accent-soft text-accent"
      : tone === "danger"
        ? "bg-danger-soft text-danger"
        : "bg-primary-soft text-primary";
  return (
    <Card className="p-5">
      <div className="flex items-center gap-3">
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconBg}`}>
          <Icon size={18} />
        </div>
        <p className="text-sm text-text-muted">{label}</p>
      </div>
      <p className="font-mono-ui mt-3 text-2xl font-medium text-text">{value}</p>
    </Card>
  );
}

export default function DashboardOverviewPage() {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((e) => setError(e.message ?? "Couldn't load statistics."))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Overview" description="A snapshot of activity across the platform right now." />

      {error && <ErrorBanner message={error} />}
      {isLoading && <LoadingBlock />}

      {stats && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            <StatCard icon={Users} label="Patients" value={stats.total_patients} />
            <StatCard icon={Users} label="Nurses" value={stats.total_nurses} />
            <StatCard icon={BadgeCheck} label="Verified nurses" value={stats.verified_nurses} />
            <StatCard
              icon={Clock}
              label="Pending verification"
              value={stats.pending_verifications}
              tone={stats.pending_verifications > 0 ? "accent" : "default"}
            />
            <StatCard icon={Activity} label="Active bookings" value={stats.active_bookings} />
            <StatCard icon={CheckCircle2} label="Completed bookings" value={stats.completed_bookings} />
            <StatCard icon={XCircle} label="Cancelled bookings" value={stats.cancelled_bookings} tone="danger" />
            <StatCard icon={Star} label="Average rating" value={stats.average_rating.toFixed(2)} />
            <StatCard icon={Wallet} label="Total revenue (paid)" value={EGP.format(stats.total_revenue)} />
            <StatCard
              icon={Percent}
              label="Commission earned"
              value={EGP.format(stats.platform_commission_earned)}
            />
          </div>

          <Card className="p-5">
            <h2 className="font-display text-lg font-semibold text-text">Most requested services</h2>
            {stats.most_requested_services.length === 0 ? (
              <p className="mt-3 text-sm text-text-muted">No care requests yet.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {stats.most_requested_services.map((row, i) => (
                  <li key={row.service} className="flex items-center gap-3">
                    <span className="font-mono-ui w-5 text-xs text-text-muted">{i + 1}</span>
                    <span className="flex-1 text-sm text-text">{row.service}</span>
                    <span className="font-mono-ui text-sm text-text-muted">{row.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
