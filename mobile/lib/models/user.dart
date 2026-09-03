/// Matches backend/app/models/user.py UserRole exactly.
enum UserRole { patient, nurse, admin }

UserRole userRoleFromApi(String v) => switch (v) {
      'PATIENT' => UserRole.patient,
      'NURSE' => UserRole.nurse,
      'ADMIN' => UserRole.admin,
      _ => throw ArgumentError('Unknown role from API: $v'),
    };

String userRoleToApi(UserRole r) => switch (r) {
      UserRole.patient => 'PATIENT',
      UserRole.nurse => 'NURSE',
      UserRole.admin => 'ADMIN',
    };

/// Mirrors backend/app/schemas/auth.py UserResponse.
class AppUser {
  final String id;
  final String email;
  final String? username;
  final String? phone;
  final UserRole role;
  final bool isActive;
  final bool isEmailVerified;
  final bool isPhoneVerified;

  const AppUser({
    required this.id,
    required this.email,
    this.username,
    this.phone,
    required this.role,
    required this.isActive,
    required this.isEmailVerified,
    required this.isPhoneVerified,
  });

  factory AppUser.fromJson(Map<String, dynamic> j) => AppUser(
        id: j['id'] as String,
        email: j['email'] as String,
        username: j['username'] as String?,
        phone: j['phone'] as String?,
        role: userRoleFromApi(j['role'] as String),
        isActive: j['is_active'] as bool,
        isEmailVerified: j['is_email_verified'] as bool,
        isPhoneVerified: j['is_phone_verified'] as bool,
      );

  String get displayName => username != null && username!.isNotEmpty
      ? username!
      : email.split('@').first;
}
