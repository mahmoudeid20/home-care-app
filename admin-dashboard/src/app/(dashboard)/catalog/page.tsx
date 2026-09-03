"use client";

import { FormEvent, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import {
  createService,
  createSpecialty,
  listServicesAdmin,
  listSpecialtiesAdmin,
  updateService,
  updateSpecialty,
} from "@/lib/api";
import type { ServiceItem, Specialty } from "@/lib/types";
import { Card, ErrorBanner, LoadingBlock, PageHeader } from "@/components/Card";
import { StatusPill } from "@/components/StatusPill";
import { Button } from "@/components/Button";

interface CatalogRow {
  id: string;
  name_en: string;
  name_ar: string;
  is_active: boolean;
}

function CatalogSection<T extends CatalogRow>({
  title,
  description,
  items,
  onCreate,
  onToggle,
}: {
  title: string;
  description: string;
  items: T[];
  onCreate: (nameEn: string, nameAr: string) => Promise<void>;
  onToggle: (item: T) => Promise<void>;
}) {
  const [showForm, setShowForm] = useState(false);
  const [nameEn, setNameEn] = useState("");
  const [nameAr, setNameAr] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onCreate(nameEn, nameAr);
      setNameEn("");
      setNameAr("");
      setShowForm(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-lg font-semibold text-text">{title}</h2>
          <p className="mt-1 text-sm text-text-muted">{description}</p>
        </div>
        <Button variant="secondary" onClick={() => setShowForm((v) => !v)} className="text-xs">
          <Plus size={14} /> Add
        </Button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mt-4 flex items-end gap-2 rounded-lg bg-gray-50 p-3">
          <div className="flex-1">
            <label className="mb-1 block text-xs text-text-muted">English name</label>
            <input
              required
              value={nameEn}
              onChange={(e) => setNameEn(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-1.5 text-sm"
            />
          </div>
          <div className="flex-1">
            <label className="mb-1 block text-xs text-text-muted">Arabic name</label>
            <input
              required
              dir="rtl"
              value={nameAr}
              onChange={(e) => setNameAr(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-1.5 text-sm"
            />
          </div>
          <Button type="submit" isLoading={isSubmitting} className="text-xs">
            Save
          </Button>
        </form>
      )}

      <ul className="mt-4 divide-y divide-border">
        {items.map((item) => (
          <li key={item.id} className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-text">{item.name_en}</p>
              <p className="text-sm text-text-muted" dir="rtl">
                {item.name_ar}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <StatusPill
                label={item.is_active ? "Active" : "Inactive"}
                tone={item.is_active ? "success" : "neutral"}
              />
              <Button
                variant="secondary"
                className="text-xs"
                isLoading={togglingId === item.id}
                onClick={async () => {
                  setTogglingId(item.id);
                  try {
                    await onToggle(item);
                  } finally {
                    setTogglingId(null);
                  }
                }}
              >
                {item.is_active ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </li>
        ))}
        {items.length === 0 && <p className="py-3 text-sm text-text-muted">Nothing here yet.</p>}
      </ul>
    </Card>
  );
}

export default function CatalogPage() {
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setIsLoading(true);
    Promise.all([listServicesAdmin(), listSpecialtiesAdmin()])
      .then(([s, sp]) => {
        setServices(s);
        setSpecialties(sp);
      })
      .catch((e) => setError(e.message ?? "Couldn't load the catalog."))
      .finally(() => setIsLoading(false));
  };

  // eslint-disable-next-line react-hooks/set-state-in-effect -- loading flag set before an async fetch is a safe, standard pattern here
  useEffect(load, []);

  return (
    <div>
      <PageHeader
        title="Services & specialties"
        description="The lists patients and nurses choose from throughout the app."
      />
      {error && <ErrorBanner message={error} />}
      {isLoading && <LoadingBlock />}
      {!isLoading && (
        <div className="grid gap-6 lg:grid-cols-2">
          <CatalogSection
            title="Services"
            description="Types of care a patient can request."
            items={services}
            onCreate={async (nameEn, nameAr) => {
              await createService({ name_en: nameEn, name_ar: nameAr, is_active: true });
              load();
            }}
            onToggle={async (item) => {
              await updateService(item.id, {
                name_en: item.name_en,
                name_ar: item.name_ar,
                is_active: !item.is_active,
              });
              load();
            }}
          />
          <CatalogSection
            title="Specialties"
            description="Nurse specialties patients can filter and match on."
            items={specialties}
            onCreate={async (nameEn, nameAr) => {
              await createSpecialty({ name_en: nameEn, name_ar: nameAr, is_active: true });
              load();
            }}
            onToggle={async (item) => {
              await updateSpecialty(item.id, {
                name_en: item.name_en,
                name_ar: item.name_ar,
                is_active: !item.is_active,
              });
              load();
            }}
          />
        </div>
      )}
    </div>
  );
}
