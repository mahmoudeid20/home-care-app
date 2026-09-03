import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../l10n/app_localizations.dart';
import '../models/user.dart';
import '../state/auth_controller.dart';
import 'home_screen.dart';
import 'bookings_screen.dart';
import 'chat_list_screen.dart';
import 'settings_screen.dart';
import 'nurse/received_requests_screen.dart';

/// Root navigation shell with IndexedStack
class RootShell extends ConsumerStatefulWidget {
  const RootShell({super.key});

  @override
  ConsumerState<RootShell> createState() => _RootShellState();
}

class _RootShellState extends ConsumerState<RootShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final role = ref.watch(authControllerProvider).user?.role;
    final isNurse = role == UserRole.nurse;

    final tabs = <int, Widget>{};
    Widget buildTab(int index) {
      return tabs.putIfAbsent(index, () => switch (index) {
        0 => isNurse ? const ReceivedRequestsScreen() : const HomeScreen(),
        1 => const BookingsScreen(),
        2 => const ChatListScreen(),
        3 => const SettingsScreen(),
        _ => const SizedBox.shrink(),
      });
    }

    return Scaffold(
      body: SafeArea(
        child: IndexedStack(
          index: _index,
          children: [
            buildTab(0),
            if (_index >= 1) buildTab(1) else const SizedBox.shrink(),
            if (_index >= 2 || tabs.containsKey(2)) buildTab(2) else const SizedBox.shrink(),
            if (_index >= 3 || tabs.containsKey(3)) buildTab(3) else const SizedBox.shrink(),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
        items: [
          BottomNavigationBarItem(
            icon: Icon(isNurse ? Icons.inbox_outlined : Icons.home_rounded),
            activeIcon: Icon(isNurse ? Icons.inbox : Icons.home_rounded),
            label: isNurse ? t.newRequests : t.navHome,
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.calendar_month_outlined),
            activeIcon: const Icon(Icons.calendar_month_rounded),
            label: t.navBookings,
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.chat_bubble_outline_rounded),
            activeIcon: const Icon(Icons.chat_bubble_rounded),
            label: t.navChat,
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.settings_outlined),
            activeIcon: const Icon(Icons.settings_rounded),
            label: t.navSettings,
          ),
        ],
      ),
    );
  }
}
