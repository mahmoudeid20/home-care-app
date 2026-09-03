"""
File type validation (Section 32). This service never handles raw file
bytes -- documents and chat attachments are represented as a URL to an
already-uploaded object in external/secure storage (Section 32: "Secure
file storage" is the storage layer's responsibility, not this API's).

What we can and do enforce here is the file extension in the URL,
rejecting obviously wrong or dangerous types (e.g. .exe, .html, .js)
before the reference is ever persisted. This is a partial mitigation, not
a substitute for real validation: true content-type sniffing and file
size limits require inspecting actual bytes, which belongs in the upload
endpoint of whatever storage service issues these URLs (S3 presigned POST
policies, a signed-upload Cloud Function, etc.) -- a piece this MVP
scaffold doesn't implement, since it only stores references.
"""
ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
ALLOWED_GENERIC_FILE_EXTENSIONS = ALLOWED_DOCUMENT_EXTENSIONS | {"txt"}


def extension_of(url: str) -> str | None:
    path = url.split("?")[0].split("#")[0]
    if "." not in path:
        return None
    return path.rsplit(".", 1)[-1].lower()


def is_allowed_extension(url: str, allowed: set[str]) -> bool:
    ext = extension_of(url)
    return ext is not None and ext in allowed


def validate_photo_url(v: str | None) -> str | None:
    """Shared pydantic validator body for optional profile-photo URL fields
    (Nurse.photo_url, Patient.photo_url) — same URL-registration pattern as
    documents/chat attachments, just restricted to image extensions."""
    if v is not None and not is_allowed_extension(v, ALLOWED_IMAGE_EXTENSIONS):
        raise ValueError(
            f"Unsupported image type. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
        )
    return v
