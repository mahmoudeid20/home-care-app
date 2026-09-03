"use client";

import { useState } from "react";
import clsx from "clsx";

/**
 * Shows a nurse/patient's uploaded photo (photo_url from the API) and
 * gracefully falls back to a colored initial if there's no photo, or the
 * image URL 404s/fails to load — mirrors the mobile app's NurseAvatar
 * widget (mobile/lib/widgets/nurse_card.dart) so both clients degrade the
 * same way.
 */
export function Avatar({
  name,
  photoUrl,
  size = 40,
}: {
  name: string;
  photoUrl?: string | null;
  size?: number;
}) {
  const [failed, setFailed] = useState(false);
  const initial = name?.trim()?.[0]?.toUpperCase() ?? "?";

  if (photoUrl && !failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- external, unpredictable object-storage URLs; next/image would require per-host config we don't control here.
      <img
        src={photoUrl}
        alt={name}
        width={size}
        height={size}
        onError={() => setFailed(true)}
        className="rounded-full object-cover border border-border"
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <span
      className={clsx(
        "flex items-center justify-center rounded-full font-semibold text-white bg-gradient-to-br from-primary to-primary-dark"
      )}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {initial}
    </span>
  );
}
