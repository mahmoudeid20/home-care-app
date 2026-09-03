import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/api_exception.dart';
import '../core/token_storage.dart';
import '../models/user.dart';
import '../services/auth_api.dart';
import '../services/patient_api.dart';

enum AuthStatus {
  bootstrapping,
  authenticated,
  needsProfileSetup,
  unauthenticated,
}

class AuthState {
  final AuthStatus status;
  final AppUser? user;
  final PatientProfile? patientProfile;

  const AuthState({
    required this.status,
    this.user,
    this.patientProfile,
  });

  const AuthState.bootstrapping() : this(status: AuthStatus.bootstrapping);
  const AuthState.unauthenticated() : this(status: AuthStatus.unauthenticated);
  const AuthState.needsProfileSetup(AppUser user)
      : this(status: AuthStatus.needsProfileSetup, user: user);
  const AuthState.authenticated(AppUser user, [PatientProfile? profile])
      : this(
          status: AuthStatus.authenticated,
          user: user,
          patientProfile: profile,
        );
}

class AuthController extends StateNotifier<AuthState> {
  AuthController() : super(const AuthState.bootstrapping()) {
    ApiClient.instance.onSessionExpired = () {
      state = const AuthState.unauthenticated();
    };
    _bootstrap();
  }

  final _api = AuthApi();
  final _patientApi = PatientApi();

  Future<void> _bootstrap() async {
    try {
      final token = await TokenStorage.instance.accessToken
          .timeout(const Duration(milliseconds: 1500), onTimeout: () => null);
      if (token == null) {
        state = const AuthState.unauthenticated();
        return;
      }
      final user = await _api.fetchCurrentUser()
          .timeout(const Duration(milliseconds: 2500));
      if (user.role == UserRole.patient) {
        final profile = await _patientApi.getMyProfile()
            .timeout(const Duration(milliseconds: 2000));
        if (profile == null) {
          state = AuthState.needsProfileSetup(user);
        } else {
          state = AuthState.authenticated(user, profile);
        }
      } else {
        state = AuthState.authenticated(user);
      }
    } catch (_) {
      await TokenStorage.instance.clear();
      state = const AuthState.unauthenticated();
    }
  }

  /// Throws ApiException on failure — the calling screen shows the message.
  Future<void> login({required String email, required String password}) async {
    final user = await _api.login(email: email, password: password);
    if (user.role == UserRole.patient) {
      final profile = await _patientApi.getMyProfile();
      if (profile == null) {
        state = AuthState.needsProfileSetup(user);
      } else {
        state = AuthState.authenticated(user, profile);
      }
    } else {
      state = AuthState.authenticated(user);
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required UserRole role,
    String? phone,
    String? username,
  }) async {
    final user = await _api.register(
      email: email,
      password: password,
      role: role,
      phone: phone,
      username: username,
    );
    if (role == UserRole.patient) {
      state = AuthState.needsProfileSetup(user);
    } else {
      state = AuthState.authenticated(user);
    }
  }

  void completeProfileSetup([PatientProfile? profile]) {
    if (state.user != null) {
      state = AuthState.authenticated(state.user!, profile);
    }
  }

  Future<void> logout() async {
    await _api.logout();
    state = const AuthState.unauthenticated();
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) => AuthController(),
);

/// Re-exported for screens that only need the exception type.
typedef AuthApiException = ApiException;
