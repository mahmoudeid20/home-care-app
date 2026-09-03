import 'package:flutter/material.dart';

/// Responsive design utilities for the Sanad app.
///
/// Uses Material Design 3 breakpoints:
/// - Compact:  < 600dp  (phones)
/// - Medium:   600-840dp (small tablets, foldables)
/// - Expanded: > 840dp  (tablets, desktops)
class Responsive {
  Responsive._();

  static const double compactBreakpoint = 600;
  static const double mediumBreakpoint = 840;

  /// Returns true if the screen width is compact (phone-sized).
  static bool isCompact(BuildContext context) =>
      MediaQuery.sizeOf(context).width < compactBreakpoint;

  /// Returns true if the screen width is medium (small tablet / foldable).
  static bool isMedium(BuildContext context) {
    final w = MediaQuery.sizeOf(context).width;
    return w >= compactBreakpoint && w < mediumBreakpoint;
  }

  /// Returns true if the screen width is expanded (tablet / desktop).
  static bool isExpanded(BuildContext context) =>
      MediaQuery.sizeOf(context).width >= mediumBreakpoint;

  /// Returns a value based on the current screen size.
  /// Example: `Responsive.value(context, compact: 20, medium: 28, expanded: 36)`
  static T value<T>(BuildContext context, {
    required T compact,
    T? medium,
    T? expanded,
  }) {
    final width = MediaQuery.sizeOf(context).width;
    if (width >= mediumBreakpoint) return expanded ?? medium ?? compact;
    if (width >= compactBreakpoint) return medium ?? compact;
    return compact;
  }

  /// Horizontal padding that scales with screen width.
  /// Phones: 20, Tablets: 32, Desktop: 48
  static double horizontalPadding(BuildContext context) =>
      value(context, compact: 20.0, medium: 32.0, expanded: 48.0);

  /// Scales a fixed size relative to screen width.
  /// Base is 375 (iPhone SE width). A value of 64 on a 375px screen
  /// becomes ~77 on a 450px screen.
  static double scale(BuildContext context, double size) {
    final width = MediaQuery.sizeOf(context).width;
    return size * (width / 375).clamp(0.85, 1.4);
  }
}
