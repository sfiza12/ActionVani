
import 'dart:convert';

/// Represents the WebSocket envelope expected by ActionVani backend.
///
/// Required fields:
/// event, session_id, request_id, data
class WebSocketMessage {
  final String event;
  final String sessionId;
  final String requestId;
  final dynamic data;

  const WebSocketMessage({
    required this.event,
    required this.sessionId,
    required this.requestId,
    required this.data,
  });

  /// Convert the message into JSON.
  Map<String, dynamic> toJson() {
    return {
      'event': event,
      'session_id': sessionId,
      'request_id': requestId,
      'data': data,
    };
  }

  /// Convert the message into a JSON string.
  String encode() {
    return jsonEncode(toJson());
  }

  /// Construct a message from a decoded JSON object.
  factory WebSocketMessage.fromJson(
    Map<String, dynamic> json,
  ) {
    const requiredFields = {
      'event',
      'session_id',
      'request_id',
      'data',
    };

    if (json.keys.toSet().length != requiredFields.length ||
        !json.keys.toSet().containsAll(requiredFields)) {
      throw const FormatException(
        'Invalid WebSocket message envelope.',
      );
    }

    final event = json['event'];
    final sessionId = json['session_id'];
    final requestId = json['request_id'];

    if (event is! String ||
        sessionId is! String ||
        requestId is! String ||
        event.trim().isEmpty ||
        sessionId.trim().isEmpty ||
        requestId.trim().isEmpty) {
      throw const FormatException(
        'Invalid WebSocket message identifiers.',
      );
    }

    return WebSocketMessage(
      event: event,
      sessionId: sessionId,
      requestId: requestId,
      data: json['data'],
    );
  }

  /// Decode a JSON string into a message.
  factory WebSocketMessage.decode(String rawMessage) {
    final decoded = jsonDecode(rawMessage);

    if (decoded is! Map<String, dynamic>) {
      throw const FormatException(
        'WebSocket response must be a JSON object.',
      );
    }

    return WebSocketMessage.fromJson(decoded);
  }
}
