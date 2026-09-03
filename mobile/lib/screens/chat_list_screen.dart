import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_exception.dart';
import '../l10n/app_localizations.dart';
import '../models/chat.dart';
import '../services/chat_api.dart';
import '../theme/app_theme.dart';
import '../widgets/error_message.dart';
import 'chat_thread_screen.dart';

final _conversationsProvider = FutureProvider.autoDispose((ref) => ChatApi().listConversations());

class ChatListScreen extends ConsumerWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(_conversationsProvider);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_conversationsProvider),
      child: CustomScrollView(slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
            child: Text(t.navChat, style: Theme.of(context).textTheme.headlineSmall),
          ),
        ),
        async.when(
          loading: () => const SliverFillRemaining(
            hasScrollBody: false,
            child: Center(child: CircularProgressIndicator()),
          ),
          error: (err, _) => SliverFillRemaining(
            hasScrollBody: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ErrorMessage(message: err is ApiException ? friendlyErrorMessage(err, t) : t.somethingWentWrong),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: () => ref.invalidate(_conversationsProvider), child: Text(t.retry)),
                ],
              ),
            ),
          ),
          data: (conversations) {
            if (conversations.isEmpty) {
              return SliverFillRemaining(
                hasScrollBody: false,
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.chat_bubble_outline, size: 56, color: AppColors.inkSoft.withOpacity(0.4)),
                      const SizedBox(height: 12),
                      Text(t.noChatsYet, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
              );
            }
            return SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              sliver: SliverList.separated(
                itemCount: conversations.length,
                separatorBuilder: (_, __) => const Divider(height: 1, color: AppColors.line),
                itemBuilder: (_, i) => _ConversationTile(conversation: conversations[i]),
              ),
            );
          },
        ),
        const SliverToBoxAdapter(child: SizedBox(height: 24)),
      ]),
    );
  }
}

class _ConversationTile extends StatelessWidget {
  final ConversationInfo conversation;
  const _ConversationTile({required this.conversation});

  @override
  Widget build(BuildContext context) {
    final initial = conversation.otherPartyName.isNotEmpty ? conversation.otherPartyName[0].toUpperCase() : '?';

    return ListTile(
      contentPadding: EdgeInsets.zero,
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ChatThreadScreen(conversation: conversation)),
      ),
      leading: Container(
        width: 44, height: 44,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(13),
          gradient: const LinearGradient(colors: [AppColors.teal500, AppColors.teal900]),
        ),
        alignment: Alignment.center,
        child: Text(initial, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
      ),
      title: Text(conversation.otherPartyName, style: Theme.of(context).textTheme.titleMedium),
      subtitle: conversation.lastMessagePreview != null
          ? Text(conversation.lastMessagePreview!, maxLines: 1, overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall)
          : null,
    );
  }
}
