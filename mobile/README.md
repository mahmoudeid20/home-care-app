# Sanad (سَنَد) — Mobile App

Flutter client for patients & nurses. Source in `lib/` is real, hand-written
Dart matching the approved design system in `../docs/design/sanad-app-prototype.html`
and `../docs/design/sanad-logo.svg`.

## Status — honest note on this sandbox

This container has no route to `pub.dev` (network is allow-listed to
`pypi.org`, `npmjs.org`, `github.com`, etc. only — see repo network policy).
That means:

- I **could** write real Dart source (done — no network needed for that).
- I **cannot** run `flutter pub get`, `flutter analyze`, `flutter test`, or
  build an APK/IPA here, because every one of those needs to fetch packages
  from pub.dev. I have not claimed otherwise and have not "verified" this
  code compiles — you should treat it as a strong, real starting point,
  not as tested output, until you run it locally or in CI with normal
  internet access.

## Run locally (once you have Flutter + internet)

Follow these exactly, in order — this is the real path from "source code"
to "running on your phone", not a generic template.

```bash
cd mobile

# 0. Recommended safety net: commit the current state first so you can
#    diff/revert if step 1 changes anything unexpected.
git init -q && git add -A && git commit -qm "starting point"

# 1. Add the missing android/ and ios/ platform folders. Safe to run on
#    top of the existing pubspec.yaml/lib/ — Flutter detects this is
#    already a Flutter project (finds pubspec.yaml + a flutter dependency)
#    and only fills in what's missing, it does not wipe lib/. Check
#    `git diff pubspec.yaml` afterward just to be sure nothing you didn't
#    expect changed.
flutter create --platforms=android,ios .

# 2. Fetch every package in pubspec.yaml
flutter pub get

# 3. Generate lib/l10n/app_localizations.dart from the .arb files
flutter gen-l10n

# 4. Generate the real app icon (assets/icons/app_icon.png, rendered from
#    the Sanad logo) for both platforms
dart run flutter_launcher_icons

# 5. Generate the native splash screen
dart run flutter_native_splash:create

# 6. Add camera/gallery permissions (image_picker needs these — they
#    don't exist until step 1 creates the native project files):
#    - android/app/src/main/AndroidManifest.xml: add inside <manifest>
#        <uses-permission android:name="android.permission.CAMERA" />
#    - ios/Runner/Info.plist: add inside the outer <dict>
#        <key>NSCameraUsageDescription</key>
#        <string>Sanad needs camera access to update your profile photo.</string>
#        <key>NSPhotoLibraryUsageDescription</key>
#        <string>Sanad needs photo library access to update your profile photo.</string>

# 7. Now the real check this whole README has been unable to do: does it
#    actually compile and pass static analysis?
flutter analyze

# 8. Point it at your backend. Either run the backend on the same machine
#    (localhost:8000 is the default — works if you're testing on an
#    Android emulator via 10.0.2.2, or on the same machine as a desktop
#    build) or pass your backend's real reachable address:
flutter run --dart-define=API_BASE_URL=http://<your-backend-host>:8000/api/v1

# --- To install on your phone specifically (not an emulator) ---
# Android: enable Developer Options + USB debugging on the phone, plug in
#   via USB, then `flutter devices` should list it — `flutter run` above
#   will install straight onto it.
# iOS: needs a Mac + Xcode + an Apple ID signed into Xcode (free personal
#   team is enough for local testing) — `flutter run` with the phone
#   plugged in and trusted works the same way.
# Alternative for Android without staying plugged in: build a standalone
#   APK and transfer it however you like (email, cloud drive, cable):
flutter build apk --dart-define=API_BASE_URL=http://<your-backend-host>:8000/api/v1
#   → produces build/app/outputs/flutter-apk/app-release.apk
#   Copy that file to the phone and open it (you'll need to allow
#   "install from unknown sources" once, since it isn't from Play Store).
```

### If `flutter analyze` in step 7 finds something

Every file here was checked by hand and by script (brace/paren balance,
every symbol used cross-referenced against its import, every localization
key cross-checked against both `.arb` files, every custom model
constructor call cross-checked against its definition) since there's no
Dart SDK in the sandbox that built this to actually run the compiler.
That's a strong basis for confidence, not a guarantee — `flutter analyze`
is the first real compiler-backed truth this code will see. If it flags
something, it's almost certainly narrow and mechanical (a renamed
parameter, a type Dart infers differently than expected) rather than a
structural problem — the architecture (providers, models, API contracts
matching the real backend schemas) has been cross-checked against the
actual backend source file-by-file throughout every slice below.

## What's implemented

- `lib/theme/app_theme.dart` — full design-token system (color, type, radii,
  component themes) matching the prototype 1:1.
- `lib/l10n/app_ar.arb`, `app_en.arb` — Arabic (default) + English strings,
  ready for `flutter gen-l10n`. Arabic drives RTL automatically via
  `Directionality`; no manual mirroring needed anywhere in the widget tree.
- `lib/screens/root_shell.dart` — bottom-nav shell using `IndexedStack` so
  tab switches are instant with no rebuild (this is what gives "fast
  navigation" — a real architectural choice, not a claim).
- `lib/screens/home_screen.dart`, `bookings_screen.dart`, `chat_list_screen.dart`,
  `profile_screen.dart` — the four tabs, with `TODO(api)` comments marking
  exactly where to wire each screen to the existing FastAPI endpoints
  (`nurse_search_service.py`, `booking_service.py`, `chat_service.py`).
- `lib/widgets/nurse_card.dart`, `nurse_summary.dart` — field names match the
  real `NurseSummary`/`NurseServiceInput` schema in `backend/app/schemas/nurse.py`,
  so wiring Dio in is a matter of an HTTP call + `.fromJson`, not a rewrite.

## Nurse profile photo (added 2026-08-30)

Nurses can now have a profile photo, end to end:

- Backend: `nurses.photo_url` column (migration `0009_add_nurse_photo_url.py`),
  exposed on `NurseResponse` (own/public profile) and `NurseSearchResult`
  (marketplace cards), settable via `POST /nurses/me` and
  `PATCH /nurses/me`. Validated server-side against
  `ALLOWED_IMAGE_EXTENSIONS` (jpg/jpeg/png/gif/webp) in `file_validation.py`
  — same "client uploads to object storage first, then registers the URL"
  pattern already used for verification documents, not a new upload
  mechanism. Covered by 4 new tests in `backend/tests/test_nurses.py`
  (set on create, rejected extension, replace on update, appears in search)
  — full suite verified at **149/149 passing** after this change.
- Mobile: `NurseAvatar` widget (`lib/widgets/nurse_card.dart`) renders the
  photo with `cached_network_image`, falling back to the gradient-initial
  avatar if `photo_url` is null or the image fails to load. Wired into
  `NurseCard` on the home tab. The nurse's own Profile tab has a tappable
  "change photo" affordance stubbed in with a `TODO(nurse-photo, api)`
  marking exactly what's left: an `image_picker` + real upload to object
  storage (S3/GCS — not built anywhere in this project yet) that returns a
  URL, then `PATCH /nurses/me`.
- **Not built**: the actual file upload endpoint/object-storage integration
  itself. Nothing in this backend accepts raw file bytes today (by design,
  see the docstring in `file_validation.py`) — that's a real remaining
  piece, not something this sandbox could fake convincingly, so I left it
  as a clearly marked TODO instead of stubbing a fake "upload succeeded".

## Auth + real API wiring (added 2026-08-30)

This is the first slice wired end-to-end to the live backend instead of demo data:

- `lib/core/api_client.dart` — single Dio instance, attaches
  `Authorization: Bearer <token>` automatically, and does a **single-flight
  silent refresh** on 401 (replays the original request once, or drops to
  the login screen if the refresh token itself is dead too).
- `lib/core/token_storage.dart` — tokens in `flutter_secure_storage`
  (Keychain/EncryptedSharedPreferences), never plain SharedPreferences.
- `lib/state/auth_controller.dart` — the one source of truth for
  "am I logged in": bootstraps by checking a stored token against
  `GET /auth/me`, exposes `login`/`register`/`logout`. `main.dart`'s
  `_AuthGate` watches this and swaps Splash → Login → RootShell with no
  screen below it needing its own auth checks.
- `lib/screens/auth/login_screen.dart`, `register_screen.dart` — real
  forms hitting `POST /auth/login` / `POST /auth/register`. Register has
  the patient/nurse role toggle (backend rejects ADMIN self-registration,
  matched client-side too) and mirrors the server's password rule
  (8+ chars, 1 letter, 1 digit) so people don't round-trip to find out.
- `lib/core/api_exception.dart` + `lib/widgets/error_message.dart` — parses
  the backend's actual error envelope (`{"error": {"code","message"}}`,
  see `app/main.py`) into a real, readable error banner instead of a
  generic "something went wrong".
- `lib/screens/home_screen.dart` — now calls `GET /nurses` for real via
  Riverpod `FutureProvider`, with proper loading spinner, error+retry
  state, and an empty state — the demo `_demoNurses` list is gone.
- Profile tab shows the real logged-in email/role and has a working
  **Log out** button (`POST /auth/logout` then clears local tokens).

### What's still fake / not wired

- Nurse tap → nurse detail screen (still a `TODO(nav)` — that's the next
  roadmap item: nurse detail + care-request + booking flow).
- Bookings and Chat tabs are unchanged from the previous slice (static
  demo content / placeholder).
- No app-level widget/integration tests were added for the auth flow —
  same limitation as before: no Dart/Flutter SDK in this sandbox at all
  (not even `dart` on PATH, let alone `flutter`), so nothing here has been
  compiled, run, or tested. I did a manual brace/paren balance sweep on
  every new file as a weak sanity check, but that is not a substitute for
  `flutter analyze` — please run that first thing once you pull this
  locally, before trusting it further than "very likely correct, unverified".

## Nurse detail + booking flow (added 2026-08-30)

Second slice wired end-to-end (in the agreed order: auth → this → chat → photo upload):

- `lib/screens/nurse_detail_screen.dart` — `GET /nurses/{id}` (full
  `NurseResponse`: bio, services with prices, specialties, verification
  flags), with loading/error/retry states. Tapping a nurse card on Home now
  actually navigates here instead of doing nothing.
- `lib/screens/care_request/care_request_form_screen.dart` — the Section 9
  patient-onboarding flow. **Design choice, not a scope cut**: implemented
  as one scrollable form with 6 numbered section headers instead of a
  literal swipeable step wizard, but every single field from
  `CareRequestCreate` (`app/schemas/care_request.py`) is present with the
  same required/optional rules the backend enforces. Submits
  `POST /care-requests`, and if opened from a nurse's profile ("Send
  request to this nurse"), immediately follows up with
  `POST /applications` to that specific nurse (Section 11 flow).
- `lib/screens/care_request/request_sent_screen.dart` — confirmation
  screen after a successful submit.
- `lib/screens/bookings_screen.dart` — now calls `GET /bookings` for real
  (the demo `_demoBookings` list, and its wrong `PENDING` booking-status
  value that doesn't exist in the backend enum, are both gone). Nurse
  names are resolved via a shared `nurseDetailProvider` (`lib/state/
  nurse_providers.dart`) so a nurse already opened from Home or a booking
  card is cached instead of re-fetched.
- New typed models for all of this: `lib/models/enums.dart` (Gender,
  PriceUnit, ShiftType, MobilityStatus, CareRequestStatus,
  ApplicationStatus, BookingStatus — every value checked 1:1 against the
  actual Python enums), `nurse_detail.dart`, `care_request.dart`,
  `application.dart`, `booking.dart`, `lookup.dart` (bilingual
  Specialty/Service — `nameFor(languageCode)` picks `name_ar`/`name_en`
  so the catalog itself follows the app's language toggle, no separate
  translation table needed).
- New API services: `lookup_api.dart` (`GET /specialties`,
  `GET /services`), `care_request_api.dart`, `application_api.dart`,
  `booking_api.dart` — same one-method-per-endpoint pattern as `auth_api.dart`.

### What's still fake / not wired

- The "matching engine" side of Section 9/21 (viewing AI-suggested nurse
  matches for an open request) isn't built — the flow here is the direct
  "send to one specific nurse from their profile" path only.
- A patient with multiple open care requests can't yet pick which one to
  attach when messaging a nurse — the form always creates a new request.
  Fine for a first booking, worth revisiting once "my care requests" list
  exists.
- Chat and photo upload are unchanged — next up per the agreed order.
- Same verification caveat as the auth slice: no Dart/Flutter SDK in this
  sandbox, so nothing here has been compiled or run. This time I went a
  step further than a brace/paren sweep — every `AppLocalizations` field
  referenced in the new code (`t.xxx`) was checked by script against both
  `.arb` files to confirm it actually exists and that Arabic/English stayed
  in lockstep (96 keys each, zero drift). That rules out one whole class of
  "compiles in English, crashes at runtime in Arabic" bug, but it is still
  not `flutter analyze` — run that first once you pull this locally.

## Real-time chat (added 2026-08-30)

Third slice (in the agreed order: auth → nurse detail/booking → **this** →
photo upload):

- `lib/services/chat_socket.dart` — thin wrapper around
  `web_socket_channel`, matches `app/websocket/chat_ws.py`'s protocol
  exactly: connects to `ws(s)://<host>/ws/conversations/{id}?token=<access
  token>` (no `/api/v1` prefix — the WS route is mounted at the app root,
  handled via a new `Env.wsBaseUrl` derived from the REST base URL rather
  than hardcoded separately), sends `{"message_type":"TEXT","content":...}`
  frames, and distinguishes the two close codes the backend actually uses
  (4401 = bad/missing token, 4403 = not a participant) from an ordinary
  network drop, so the UI can show "you don't have access" instead of a
  useless "reconnecting" spinner for a conversation that will never connect.
- `lib/screens/chat_thread_screen.dart` — preloads history via
  `GET /conversations/{id}/messages`, then opens the socket for live
  delivery. Sends go through the socket when connected; if the socket is
  down, falls back to `POST /conversations/{id}/messages` (the backend's
  own documented REST fallback) instead of silently dropping the message.
  Deliberately does **not** optimistically append the sent message locally
  when the socket is live — the server broadcasts the persisted message
  back to the sender too, so appending twice would show a duplicate. This
  was an actual bug I caught while re-reading `chat_ws.py`'s broadcast
  logic before writing the send method, not something a test caught (there
  are no tests here) — worth flagging since it's exactly the kind of thing
  that would only surface after a real device sent a real message and saw
  it show up twice.
- `lib/screens/chat_list_screen.dart` — real `GET /conversations`,
  replacing the empty placeholder.
- Nurse detail screen now has a working "Message" button next to "Send
  request" — calls `POST /conversations` (idempotent per patient+nurse
  pair per the backend) and opens straight into the thread.
- `lib/models/chat.dart` — `ConversationInfo`/`ChatMessage`, matching
  `app/schemas/chat.py` field-for-field, including the enum-safety pattern
  used everywhere else in this app (`MessageType` mapped to/from the exact
  `TEXT`/`IMAGE`/`FILE` strings the backend uses).

### What's still fake / not wired

- Only TEXT messages have a compose UI; the socket/REST layers already
  support IMAGE (`sendImage`), but there's no attachment picker yet — that
  naturally lands together with the next item (photo upload), since both
  need the same "pick a file → upload to object storage → get back a URL"
  flow.
- No typing indicators, read receipts, or push notification on new
  message — none of those exist on the backend either (Section 20's MVP
  scope is send/receive + REST fallback only), so nothing was cut here,
  they're just not built anywhere yet.
- Same verification method as the last two slices: brace/paren balance
  sweep (clean) + a script cross-checking every `t.xxx` localization call
  in the whole `lib/screens` and `lib/widgets` tree against both `.arb`
  files (102 keys each, zero missing, zero drift between languages). Still
  not `flutter analyze` — no Dart SDK in this sandbox to run it.

## Photo upload from the device (added 2026-08-30)

Fourth slice — the last one from the original priority list (auth → nurse
detail/booking → chat → **this**):

- `lib/services/object_storage_uploader.dart` — an `ObjectStorageUploader`
  interface plus the one piece that genuinely cannot be built without a
  decision from you: **no object storage provider is configured anywhere
  in this project** (confirmed again while building this — grep the whole
  repo for S3/Firebase Storage/Cloudinary and there's nothing). The default
  wired-in implementation throws a clear `StorageNotConfiguredException`
  instead of pretending to succeed. Swapping in a real uploader (S3
  presigned PUT, Firebase Storage, Cloudinary, ...) is a one-line change
  in `profile_screen.dart` where `_uploader` is constructed — the picker,
  local-preview, error-handling, and PATCH-to-backend code around it don't
  change.
- `lib/screens/profile_screen.dart` — the camera-badge tap now actually
  works: `image_picker` bottom sheet (camera or gallery) → local preview
  shown immediately → upload attempt → on success, `PATCH /nurses/me` or
  `/patients/me` with the resulting `photo_url` (role-aware, reusing the
  server-side validation already added in the earlier "nurse profile
  photo" backend work — same `ALLOWED_IMAGE_EXTENSIONS` check applies).
  On `StorageNotConfiguredException` specifically, shows an honest
  in-app message ("photo upload isn't available yet") rather than a
  generic error, since that's not really an error — it's an unbuilt
  dependency.
- `lib/services/patient_api.dart` — new, `PATCH /patients/me` for the
  photo field (nurse side already had the equivalent via `NurseApi`).

### Important gap noticed while wiring this in

This `mobile/` folder has never had `flutter create .` run on it (no
Flutter SDK here to run it with) — there's a `lib/`, `pubspec.yaml`, and
`l10n.yaml`, but **no `android/` or `ios/` platform folders**. That
matters specifically for `image_picker`: camera/gallery access needs
native permission entries (`NSCameraUsageDescription`/
`NSPhotoLibraryUsageDescription` in `Info.plist`, `<uses-permission>` for
camera in `AndroidManifest.xml`) that don't exist yet because those files
don't exist yet. First real step once you have Flutter locally:
`flutter create .` from inside `mobile/` (safe — it only adds the missing
platform folders, doesn't touch `lib/`), then add those permission
entries before this screen will actually prompt for camera/gallery access
instead of crashing.

### What's still fake / not wired

- The object storage provider itself (see above) — this is now the single
  concrete blocker for photos actually working end-to-end, once you pick
  a provider I can wire the real implementation in.
- Chat's `sendImage` (already built into `ChatSocket`) still has no
  attachment-picker UI in `chat_thread_screen.dart` — same missing
  uploader blocks it, so it made sense to land both against the same
  interface rather than build two different half-solutions.
- Same verification method as the last three slices: brace/paren balance
  sweep (clean), every `t.xxx` checked against both `.arb` files (108 keys
  each, zero drift), and every relative import checked to resolve to a
  real file. Still not `flutter analyze` or an actual run on a device —
  no Dart/Flutter SDK in this sandbox, and as of this slice, not even the
  native platform folders exist yet for this specific feature to be
  testable even if the SDK were here.

## Nurse-side screens (added 2026-08-31)

Fifth slice. This one started with a real backend gap, not just mobile work:

- **Backend fix**: `GET /care-requests/{id}` was patient-owner-only —
  there was genuinely no way for a nurse to see what they were being
  asked to do before accepting/rejecting a request (Section 18's "New
  Requests" needs this). Fixed in `care_request_service.py` (`get()` now
  allows either the owning patient or a nurse with *any* application —
  pending, accepted, rejected, or withdrawn — for that request) and the
  router (`require_roles(PATIENT, NURSE)`). Mutating operations
  (`update`/`cancel`) deliberately stay patient-only via the untouched
  `_get_owned`. Added `ApplicationRepository.get_any_for_nurse_and_request`
  (the existing `get_active_for_nurse_and_request` only matches PENDING,
  which is correct for its own job of blocking duplicate applications, but
  wrong for read access — a nurse who already rejected a request should
  still be able to look back at what they rejected). Two new tests (access
  granted after applying, still forbidden for an unrelated nurse) — full
  suite verified at **153/153 passing**.
- `lib/screens/nurse/received_requests_screen.dart` — Section 18's "New
  Requests" list, wired to `GET /applications/received`.
- `lib/screens/nurse/application_detail_screen.dart` — fetches the full
  care request via the now-fixed endpoint, shows patient info/condition/
  location/schedule/budget, and for PENDING applications, Accept (with a
  confirm dialog, since it creates a real Booking server-side) / Reject
  (with an optional reason, matching `ApplicationRejectRequest`).
- `lib/screens/root_shell.dart` — the Home tab is now role-aware: a nurse
  sees `ReceivedRequestsScreen` in that slot instead of the patient's
  nurse-search `HomeScreen`. Bookings/Chat/Profile stay shared since
  `GET /bookings` and `GET /conversations` are already scoped server-side
  by role — no client-side duplication needed there.
- `ApplicationApi` extended with `listReceived`, `accept`, `reject` (nurse
  actions) alongside the existing `send`/`withdraw` (patient actions).
  `CareRequestApi.getById` and a new `CareRequestDetail` model added for
  the detail view.

### What's still fake / not wired

- A patient's own "sent requests" list (`GET /applications/sent` — the API
  method exists in `ApplicationApi.listSent`) has no screen yet; right now
  a patient only sees the *outcome* via their Bookings tab once a nurse
  accepts.
- Reviews (leaving one after a REVIEWED-eligible booking) — next in line.
- Same verification method as every slice so far: brace/paren balance
  sweep (clean), every `t.xxx` cross-checked against both `.arb` files
  (123 keys each, zero drift), every relative import resolved. The
  backend half of this slice is different and stronger: real pytest run
  against a real (if SQLite, per-test) database, not a static sweep —
  153/153, including the two new access-control tests.

## Sent requests + reviews (added 2026-08-31)

Sixth slice — no backend changes needed this round, both endpoints
already existed and matched what was expected:

- `lib/screens/patient/sent_requests_screen.dart` — `GET /applications/sent`,
  reachable via a new "My sent requests" link on the patient's Bookings
  tab header (patients only — hidden for a nurse-role session). Pending
  requests get a Withdraw action (`POST /applications/{id}/withdraw`),
  matching the backend's own PENDING-only restriction on that endpoint
  (attempting it on an already-accepted/rejected request would 422, so
  the button only renders for PENDING in the first place rather than
  showing it and letting the request fail).
- `lib/screens/leave_review_screen.dart` — four separate 1-5 star ratings
  (overall, professionalism, communication, care quality) plus an
  optional comment, matching `ReviewCreate` field-for-field. Reachable
  from a COMPLETED booking card's new "Leave a review" button on the
  Bookings tab. Specifically handles the backend's 409 ("already
  reviewed this booking") with its own message instead of a generic
  retry-suggesting error, since retrying a 409 can't succeed.
  `lib/services/review_api.dart` + `lib/models/review.dart` added,
  matching `app/schemas/review.py`.
- `ApplicationApi.listSent` was already there from the previous slice
  (added alongside `listReceived` even though nothing used it yet) — this
  is the screen that finally uses it.

### What's still fake / not wired in this slice

- A nurse's own review list (`GET /nurses/{id}/reviews`, wrapped by
  `ReviewApi.listForNurse`) has a service method but isn't displayed
  anywhere yet — the nurse detail screen's "Reviews" section header exists
  in the UI copy but the list under it was never actually built.
- Same verification method as every slice: brace/paren balance (clean),
  every `t.xxx` cross-checked against both `.arb` files (136 keys each,
  zero drift), every relative import resolved, and the backend test suite
  re-run to confirm nothing regressed (still 153/153 — no backend files
  were touched this round, so that's expected, not a new result).

## Bug fixes + nurse reviews list (added 2026-08-31)

Seventh slice. This one is different from the others: it's mostly a
verification pass that caught real problems, plus finishing the one gap
flagged at the end of the last slice.

- **Two real missing-import bugs found and fixed** in
  `screens/nurse_detail_screen.dart`: it used `ApiException`/
  `friendlyErrorMessage()` without importing `core/api_exception.dart`,
  and used `NurseAvatar` without importing `widgets/nurse_card.dart`.
  Both would have failed to compile immediately — caught this time by a
  purpose-built script (not the balance/import checks used in earlier
  slices, which only check that *declared* imports resolve to real files,
  not that everything *used* is actually imported) that cross-references
  every use of ~45 shared symbols (`ApiException`, `AppColors`,
  `NurseCard`, etc.) against each file's import list, with comments
  stripped first so a symbol only mentioned in a `//` note doesn't count
  as a false positive. Re-ran it project-wide afterward: zero remaining
  issues. This is now part of the standard verification pass for every
  future slice, not a one-off.
- `lib/screens/nurse_detail_screen.dart` — the "Reviews" section (title
  already existed, list under it didn't) now actually calls
  `GET /nurses/{id}/reviews` via the `ReviewApi.listForNurse` method that
  was added but unused in the previous slice, and renders each review's
  star rating + comment.

### Verification for this slice

Balance sweep (clean), the new symbol-import cross-check (0 issues,
project-wide), every `t.xxx` checked against both `.arb` files (137 keys
each, zero drift), every relative import resolved, and the backend suite
re-run to confirm the untouched backend is still green (153/153 — no
backend files changed this round).

## Deep compile-risk audit + real app icon/splash (added 2026-09-01)

Eighth slice, prompted directly by "I want zero mistakes, everything
wired, ready to actually run on my phone." Two different kinds of work:

**A harder audit pass than any previous slice.** The symbol-import
cross-check from the last slice only catches missing imports; it says
nothing about whether the *APIs themselves* are used correctly. This pass
specifically hunted for that class of bug, and found three real ones:

- `DropdownButtonFormField` was using `initialValue:` in three places in
  `care_request_form_screen.dart`. That parameter only exists on recent
  Flutter — the declared SDK floor (`>=3.3.0`) covered versions where it
  doesn't, which would be a hard compile error, not a warning. Changed to
  `value:`, which has worked across every Flutter version that matters
  here.
- Same root cause the other direction: `AppTheme` used `CardThemeData`
  (only guaranteed on quite recent Flutter) while still declaring the old
  `>=3.3.0` floor. Rather than rewrite every borderline-new API back to
  something older and uglier, I raised the floor to `>=3.24.0` — anyone
  installing Flutter fresh today is far past that anyway, so this trades
  a real compile risk for zero practical cost.
- `go_router` was declared in `pubspec.yaml` and never used anywhere
  (every screen navigates via plain `Navigator.push`) — removed. Not a
  bug, but "every dependency declared is actually used" is part of what
  "no mistakes" means for a project someone's about to build for real.
- A scripted, project-wide cross-check: every custom model's constructor
  call (`NurseSummary(...)`, `BookingInfo(...)`, `LocationData(...)`,
  etc.) verified against its actual constructor definition — 0 real
  mismatches (one script false-positive from a ternary `? … : null`
  confusing the arg-name regex, checked by hand and confirmed harmless).
  Also verified: every `Icons.xxx` name used is a real Material icon
  (23 distinct icons, all checked), every relative import path to the
  generated `app_localizations.dart` resolves correctly regardless of
  how deep the importing file is nested, and every `mounted`/
  `context.mounted` guard is used inside a class that actually has that
  member.

**Real app icon + splash screen, not just SVGs someone would need to
convert later.** `assets/icons/app_icon.png` and `app_icon_foreground.png`
are actual rendered 1024×1024 PNGs (via `rsvg-convert`, installed for
this), generated from the Sanad logo mark — not placeholders. Wired
`flutter_launcher_icons` and `flutter_native_splash` into `pubspec.yaml`
with real, specific config (Sanad's actual brand colors, not defaults) so
`dart run flutter_launcher_icons` / `flutter_native_splash:create`
produce the real app icon and splash screen on both platforms the first
time they're run — see the updated step-by-step above.

### What I still can't do from here, and what I'd need to go further

- **Nothing more can be verified in this sandbox.** Every remaining risk
  is now the kind that only a real Dart compiler run (`flutter analyze`)
  can catch — I've exhausted what static, non-compiler checking can find.
- **Object storage** (real photo upload) and **push notifications** (real
  FCM) both need a provider decision + credentials from you — see the
  earlier slices' notes on exactly what each needs. Neither blocks
  running or testing the rest of the app; photo upload shows an honest
  "not set up yet" message instead of failing silently, and nothing calls
  the (stub) push path during normal use.
- **Widget/integration tests** and **App Store/Play Store publishing**
  need the Dart SDK and your own developer accounts respectively — both
  are things to do after step 7 (`flutter analyze`) above confirms the
  code compiles clean on your machine.

## What's not implemented yet

An object storage provider connected (the concrete blocker for photo/image
upload actually working), push-notification wiring (backend's
`fcm_client.py` is also still a stub), widget/integration tests, and
app store publish setup (signing, store listings). `flutter create .`,
icon/splash generation, and `flutter analyze` are now precise, ready-to-run
steps in the guide above rather than open TODOs.
