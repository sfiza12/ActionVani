import 'dart:async';
import 'dart:math';

import '../websocket/websocket_client.dart';
import '../websocket/websocket_message.dart';

class SessionService {
  SessionService({
  required this._webSocketClient,
});

  final WebSocketClient _webSocketClient;
  final Random _random = Random.secure();

  String? _sessionId;
  int _requestCounter = 0;
  bool _disposed = false;

  String? get sessionId => _sessionId;

  bool get isConnected => _webSocketClient.isConnected;

  Stream<WebSocketMessage> get messages =>
      _webSocketClient.messages;

  Stream<WebSocketConnectionState> get connectionStates =>
      _webSocketClient.connectionStates;

  String _generateId(String prefix) {
    final timestamp = DateTime.now().microsecondsSinceEpoch;
    final randomPart = _random.nextInt(1 << 32);

    return '${prefix}_${timestamp}_$randomPart';
  }

  /// Creates a local session and connects to the backend.
  Future<String> startSession() async {
    if (_disposed) {
      throw StateError('SessionService has been disposed.');
    }

    if (isConnected && _sessionId != null) {
      return _sessionId!;
    }

    _sessionId ??= _generateId('session');

    await _webSocketClient.connect();

    return _sessionId!;
  }

  /// Sends an event using the existing backend envelope.
  ///
  /// Event names and data structures must be agreed
  /// with the backend team before production integration.
  String sendEvent({
    required String event,
    required dynamic data,
  }) {
    if (_disposed) {
      throw StateError('SessionService has been disposed.');
    }

    if (!isConnected || _sessionId == null) {
      throw StateError('No active connected session.');
    }

    _requestCounter++;

    final requestId =
        'request_${_requestCounter}_${_random.nextInt(1 << 32)}';

    final message = WebSocketMessage(
      event: event,
      sessionId: _sessionId!,
      requestId: requestId,
      data: data,
    );

    _webSocketClient.sendMessage(message);

    return requestId;
  }

  /// Ends the local session and closes the connection.
  Future<void> endSession() async {
    _sessionId = null;
    _requestCounter = 0;

    await _webSocketClient.disconnect();
  }

  /// Releases the service and its WebSocket resources.
  Future<void> dispose() async {
    if (_disposed) return;

    await endSession();
    await _webSocketClient.dispose();

    _disposed = true;
  }
}