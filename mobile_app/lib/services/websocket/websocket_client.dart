
import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import 'websocket_message.dart';

enum WebSocketConnectionState {
  disconnected,
  connecting,
  connected,
  error,
}

class WebSocketClient {
  WebSocketClient({
    required this.serverUrl,
  });

  final String serverUrl;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;

  final StreamController<WebSocketMessage> _messageController =
      StreamController<WebSocketMessage>.broadcast();

  final StreamController<WebSocketConnectionState>
      _stateController =
      StreamController<WebSocketConnectionState>.broadcast();

  WebSocketConnectionState _state =
      WebSocketConnectionState.disconnected;

  bool _disposed = false;
  bool _intentionalDisconnect = false;

  /// Stream of messages received from the backend.
  Stream<WebSocketMessage> get messages =>
      _messageController.stream;

  /// Stream of connection status updates.
  Stream<WebSocketConnectionState> get connectionStates =>
      _stateController.stream;

  /// Current connection status.
  WebSocketConnectionState get state => _state;

  bool get isConnected =>
      _state == WebSocketConnectionState.connected;

  void _updateState(WebSocketConnectionState newState) {
    if (_disposed) return;

    _state = newState;

    if (!_stateController.isClosed) {
      _stateController.add(newState);
    }
  }

  /// Connect to the ActionVani FastAPI WebSocket endpoint.
  Future<void> connect() async {
    if (_disposed) {
      throw StateError('WebSocketClient has been disposed.');
    }

    if (_state == WebSocketConnectionState.connected ||
        _state == WebSocketConnectionState.connecting) {
      return;
    }

    _intentionalDisconnect = false;

    _updateState(WebSocketConnectionState.connecting);

    try {
      final uri = Uri.parse(serverUrl);

      if (uri.scheme != 'ws' && uri.scheme != 'wss') {
        throw ArgumentError(
          'WebSocket URL must use ws:// or wss://',
        );
      }

      _channel = WebSocketChannel.connect(uri);

      // Wait until the WebSocket handshake succeeds.
      await _channel!.ready;

      if (_disposed || _intentionalDisconnect) {
        await _channel!.sink.close();
        return;
      }

      _updateState(WebSocketConnectionState.connected);

      _subscription = _channel!.stream.listen(
        _handleIncomingMessage,
        onError: (error) {
          _updateState(WebSocketConnectionState.error);
        },
        onDone: () {
          if (!_intentionalDisconnect && !_disposed) {
            _updateState(
              WebSocketConnectionState.disconnected,
            );
          }
        },
        cancelOnError: false,
      );
    } catch (error) {
      _updateState(WebSocketConnectionState.error);
      rethrow;
    }
  }

  /// Send a valid ActionVani message envelope.
  void sendMessage(WebSocketMessage message) {
    if (!isConnected || _channel == null) {
      throw StateError(
        'Cannot send message: WebSocket is not connected.',
      );
    }

    final encodedMessage = message.encode();

    _channel!.sink.add(encodedMessage);
  }

  /// Handle incoming backend messages.
  void _handleIncomingMessage(dynamic rawMessage) {
    if (_disposed || _messageController.isClosed) {
      return;
    }

    try {
      if (rawMessage is! String) {
        throw const FormatException(
          'Expected a text WebSocket message.',
        );
      }

      final message = WebSocketMessage.decode(rawMessage);

      _messageController.add(message);
    } catch (error, stackTrace) {
      _messageController.addError(error, stackTrace);
    }
  }

  /// Disconnect from the backend.
  Future<void> disconnect() async {
    _intentionalDisconnect = true;

    await _subscription?.cancel();
    _subscription = null;

    await _channel?.sink.close(1000);
    _channel = null;

    if (!_disposed) {
      _updateState(WebSocketConnectionState.disconnected);
    }
  }

  /// Release all resources.
  Future<void> dispose() async {
    if (_disposed) return;

    await disconnect();

    _disposed = true;

    await _messageController.close();
    await _stateController.close();
  }
}
