import 'dart:io';

/// The one missing piece across this whole project (see backend's
/// file_validation.py docstring and mobile/README.md): every profile-photo
/// and chat-attachment field expects a URL that already lives in secure
/// object storage. Nothing in this codebase — backend or mobile — actually
/// hosts files; this interface is where "upload the bytes somewhere real"
/// plugs in once a provider (S3, Firebase Storage, Cloudinary, ...) is
/// chosen and its credentials are available.
abstract class ObjectStorageUploader {
  /// Uploads [file] and returns its public/signed URL, ready to hand
  /// straight to PATCH /nurses/me, /patients/me, or a chat IMAGE message.
  Future<String> upload(File file);
}

/// Thrown by [UnconfiguredObjectStorageUploader] so call sites can show a
/// clear, honest message ("photo upload isn't set up yet") instead of a
/// generic network-error banner that implies something is broken rather
/// than simply not built.
class StorageNotConfiguredException implements Exception {
  @override
  String toString() =>
      'No object storage provider is configured. Swap ObjectStorageUploader '
      'for a real implementation (S3 presigned PUT, Firebase Storage, '
      'Cloudinary, etc.) — see lib/services/object_storage_uploader.dart.';
}

/// Default wired-in implementation until a real provider is chosen.
/// Every call site (ProfileScreen's photo picker, chat's future image
/// attachment) already goes through the [ObjectStorageUploader] interface,
/// so replacing this is a one-line change wherever it's constructed —
/// not a rewrite of the picker/upload/PATCH flow around it.
class UnconfiguredObjectStorageUploader implements ObjectStorageUploader {
  @override
  Future<String> upload(File file) async {
    throw StorageNotConfiguredException();
  }
}
