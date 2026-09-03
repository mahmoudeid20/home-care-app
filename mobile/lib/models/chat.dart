enum MessageType { text, image, file }

String messageTypeToApi(MessageType t) => switch (t) {
      MessageType.text => 'TEXT',
      MessageType.image => 'IMAGE',
      MessageType.file => 'FILE',
    };

MessageType messageTypeFromApi(String v) => switch (v) {
      'IMAGE' => MessageType.image,
      'FILE' => MessageType.file,
      _ => MessageType.text,
    };

/// Mirrors ConversationResponse in app/schemas/chat.py. `otherPartyName`
/// is already resolved server-side to whichever party the caller isn't —
/// the client never has to figure out "is this a patient or nurse view".
class ConversationInfo {
  final String id;
  final String patientId;
  final String nurseId;
  final String? bookingId;
  final String otherPartyName;
  final String? lastMessagePreview;
  final DateTime? lastMessageAt;

  const ConversationInfo({
    required this.id,
    required this.patientId,
    required this.nurseId,
    this.bookingId,
    required this.otherPartyName,
    this.lastMessagePreview,
    this.lastMessageAt,
  });

  factory ConversationInfo.fromJson(Map<String, dynamic> j) => ConversationInfo(
        id: j['id'] as String,
        patientId: j['patient_id'] as String,
        nurseId: j['nurse_id'] as String,
        bookingId: j['booking_id'] as String?,
        otherPartyName: j['other_party_name'] as String,
        lastMessagePreview: j['last_message_preview'] as String?,
        lastMessageAt: j['last_message_at'] != null ? DateTime.parse(j['last_message_at'] as String) : null,
      );
}

/// Mirrors MessageResponse. [isMine] is computed by the caller (compares
/// senderId to the logged-in user's id) since the server has no concept
/// of "mine" — it's purely a client-side display detail.
class ChatMessage {
  final String id;
  final String conversationId;
  final String senderId;
  final MessageType type;
  final String? content;
  final String? attachmentUrl;
  final DateTime createdAt;

  const ChatMessage({
    required this.id,
    required this.conversationId,
    required this.senderId,
    required this.type,
    this.content,
    this.attachmentUrl,
    required this.createdAt,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> j) => ChatMessage(
        id: j['id'] as String,
        conversationId: j['conversation_id'] as String,
        senderId: j['sender_id'] as String,
        type: messageTypeFromApi(j['message_type'] as String),
        content: j['content'] as String?,
        attachmentUrl: j['attachment_url'] as String?,
        createdAt: DateTime.parse(j['created_at'] as String),
      );
}
