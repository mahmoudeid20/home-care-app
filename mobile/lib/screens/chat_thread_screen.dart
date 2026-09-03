import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_exception.dart';
import '../l10n/app_localizations.dart';
import '../models/chat.dart';
import '../services/chat_api.dart';
import '../services/chat_socket.dart';
import '../state/auth_controller.dart';
import '../theme/app_theme.dart';
import '../widgets/error_message.dart';

class ChatThreadScreen extends ConsumerStatefulWidget {
  final ConversationInfo conversation;
  const ChatThreadScreen({super.key, required this.conversation});

  @override
  ConsumerState<ChatThreadScreen> createState() => _ChatThreadScreenState();
}

enum _ConnState { connecting, live, reconnecting, forbidden }

class _ChatThreadScreenState extends ConsumerState<ChatThreadScreen> {
  final _api = ChatApi();
  final _socket = ChatSocket();
  final _inputCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  final List<ChatMessage> _messages = [];
  bool _loadingHistory = true;
  String? _historyError;
  _ConnState _connState = _ConnState.connecting;

  @override
  void initState() {
    super.initState();
    _loadHistoryThenConnect();
  }

  @override
  void dispose() {
    _socket.dispose();
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadHistoryThenConnect() async {
    try {
      final history = await _api.listMessages(widget.conversation.id);
      if (!mounted) return;
      setState(() {
        // Backend returns newest-first-or-last depending on offset paging;
        // normalize to chronological (oldest first) for a top-to-bottom list.
        _messages
          ..clear()
          ..addAll(history.reversed);
        _loadingHistory = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _historyError = e.message;
        _loadingHistory = false;
      });
      return;
    }
    _connect();
  }

  void _connect() {
    _socket.onAuthError = () {
      if (mounted) setState(() => _connState = _ConnState.forbidden);
    };
    _socket.onDisconnected = () {
      if (mounted) setState(() => _connState = _ConnState.reconnecting);
    };
    _socket.messages.listen((m) {
      if (!mounted) return;
      setState(() => _messages.add(m));
      _scrollToBottom();
    });
    _socket.connect(widget.conversation.id).then((_) {
      if (mounted && _socket.isConnected) setState(() => _connState = _ConnState.live);
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollCtrl.hasClients) return;
      _scrollCtrl.animateTo(
        _scrollCtrl.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _send() async {
    final text = _inputCtrl.text.trim();
    if (text.isEmpty) return;
    _inputCtrl.clear();

    if (_socket.isConnected) {
      // Optimistic-free by design: we don't locally append here. The
      // server broadcasts the persisted message back to every connected
      // participant including the sender, so appending twice would show
      // a duplicate. If the socket is down we fall back to REST below,
      // which *does* need a local append since there's no broadcast.
      _socket.sendText(text);
      return;
    }

    try {
      final sent = await _api.sendMessageRest(widget.conversation.id, type: MessageType.text, content: text);
      if (!mounted) return;
      setState(() => _messages.add(sent));
      _scrollToBottom();
    } on ApiException catch (_) {
      if (!mounted) return;
      setState(() => _inputCtrl.text = text); // give the text back so nothing is lost
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final myUserId = ref.watch(authControllerProvider).user?.id;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.conversation.otherPartyName, style: const TextStyle(fontSize: 16)),
        bottom: _connState == _ConnState.reconnecting
            ? PreferredSize(
                preferredSize: const Size.fromHeight(22),
                child: _StatusBanner(text: t.reconnecting, color: AppColors.amberDark),
              )
            : _connState == _ConnState.forbidden
                ? PreferredSize(
                    preferredSize: const Size.fromHeight(22),
                    child: _StatusBanner(text: t.cantAccessConversation, color: AppColors.danger),
                  )
                : null,
      ),
      body: Column(
        children: [
          Expanded(
            child: _loadingHistory
                ? const Center(child: CircularProgressIndicator())
                : _historyError != null
                    ? Center(child: ErrorMessage(message: _historyError!))
                    : ListView.builder(
                        controller: _scrollCtrl,
                        padding: const EdgeInsets.all(16),
                        itemCount: _messages.length,
                        itemBuilder: (_, i) {
                          final m = _messages[i];
                          final mine = m.senderId == myUserId;
                          return _Bubble(message: m, mine: mine);
                        },
                      ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 10),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _inputCtrl,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _send(),
                      decoration: InputDecoration(
                        hintText: t.messageHint,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _send,
                    icon: const Icon(Icons.send_rounded, size: 18),
                    style: IconButton.styleFrom(backgroundColor: AppColors.teal700, foregroundColor: Colors.white),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  final String text;
  final Color color;
  const _StatusBanner({required this.text, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 22,
      width: double.infinity,
      color: color.withOpacity(0.12),
      alignment: Alignment.center,
      child: Text(text, style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700, color: color)),
    );
  }
}

class _Bubble extends StatelessWidget {
  final ChatMessage message;
  final bool mine;
  const _Bubble({required this.message, required this.mine});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
        decoration: BoxDecoration(
          color: mine ? AppColors.teal700 : AppColors.surface,
          border: mine ? null : Border.all(color: AppColors.line),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(mine ? 16 : 4),
            bottomRight: Radius.circular(mine ? 4 : 16),
          ),
        ),
        child: Text(
          message.content ?? '',
          style: TextStyle(fontSize: 12.5, height: 1.5, color: mine ? Colors.white : AppColors.ink),
        ),
      ),
    );
  }
}
