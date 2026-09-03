"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  getMatchingWeights,
  getPlatformSettings,
  updateMatchingWeights,
  updatePlatformSettings,
} from "@/lib/api";
import type { MatchingWeights, PlatformSettings } from "@/lib/types";
import { Card, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";
import { Button } from "@/components/Button";

const WEIGHT_LABELS: { key: keyof MatchingWeights; label: string }[] = [
  { key: "skills_weight", label: "Skills match" },
  { key: "experience_weight", label: "Experience" },
  { key: "location_weight", label: "Location / distance" },
  { key: "availability_weight", label: "Availability" },
  { key: "price_weight", label: "Price compatibility" },
  { key: "rating_weight", label: "Rating" },
  { key: "verification_weight", label: "Verification" },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<PlatformSettings | null>(null);
  const [weights, setWeights] = useState<MatchingWeights | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);
  const [savingWeights, setSavingWeights] = useState(false);

  useEffect(() => {
    Promise.all([getPlatformSettings(), getMatchingWeights()])
      .then(([s, w]) => {
        setSettings(s);
        setWeights(w);
      })
      .catch((e) => setError(e.message ?? "Couldn't load settings."))
      .finally(() => setIsLoading(false));
  }, []);

  const handleSaveCommission = async (e: FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    setSavingSettings(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updatePlatformSettings(settings.commission_percentage);
      setSettings(updated);
      setMessage("Commission percentage updated.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Couldn't save.");
    } finally {
      setSavingSettings(false);
    }
  };

  const weightsSum = weights ? Object.values(weights).reduce((a, b) => a + Number(b), 0) : 0;

  const handleSaveWeights = async (e: FormEvent) => {
    e.preventDefault();
    if (!weights) return;
    setSavingWeights(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateMatchingWeights(weights);
      setWeights(updated);
      setMessage("Matching weights updated.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Weights must sum to 100%.");
    } finally {
      setSavingWeights(false);
    }
  };

  return (
    <div>
      <PageHeader title="Settings" description="Platform-wide configuration." />

      {error && <ErrorBanner message={error} />}
      {message && (
        <div className="mb-4 rounded-lg bg-success-soft px-4 py-3 text-sm text-success">
          {message}
        </div>
      )}
      {isLoading && <LoadingBlock />}

      {!isLoading && settings && (
        <Card className="mb-6 p-5">
          <h2 className="font-display text-lg font-semibold text-text">Commission</h2>
          <p className="mt-1 text-sm text-text-muted">
            Percentage of each completed booking&apos;s price the platform keeps.
          </p>
          <form onSubmit={handleSaveCommission} className="mt-4 flex items-end gap-3">
            <div>
              <label className="mb-1 block text-xs text-text-muted">Commission %</label>
              <input
                type="number"
                min={0}
                max={100}
                step={1}
                value={Math.round(settings.commission_percentage * 100)}
                onChange={(e) =>
                  setSettings({ commission_percentage: Number(e.target.value) / 100 })
                }
                className="w-28 rounded-lg border border-border bg-white px-3 py-1.5 text-sm"
              />
            </div>
            <Button type="submit" isLoading={savingSettings} className="text-sm">
              Save
            </Button>
          </form>
        </Card>
      )}

      {!isLoading && weights && (
        <Card className="p-5">
          <h2 className="font-display text-lg font-semibold text-text">Matching engine weights</h2>
          <p className="mt-1 text-sm text-text-muted">
            How much each factor contributes to a nurse&apos;s match score. Must sum to 100%.
          </p>
          <form onSubmit={handleSaveWeights} className="mt-4 space-y-3">
            {WEIGHT_LABELS.map(({ key, label }) => (
              <div key={key} className="flex items-center justify-between gap-4">
                <label className="text-sm text-text">{label}</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={1}
                    value={Math.round(weights[key] * 100)}
                    onChange={(e) => setWeights({ ...weights, [key]: Number(e.target.value) / 100 })}
                    className="w-20 rounded-lg border border-border bg-white px-3 py-1.5 text-sm"
                  />
                  <span className="text-sm text-text-muted">%</span>
                </div>
              </div>
            ))}
            <div className="flex items-center justify-between border-t border-border pt-3">
              <span
                className={`text-sm font-medium ${
                  Math.round(weightsSum * 100) === 100 ? "text-success" : "text-danger"
                }`}
              >
                Total: {Math.round(weightsSum * 100)}%
              </span>
              <Button type="submit" isLoading={savingWeights} className="text-sm">
                Save weights
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
