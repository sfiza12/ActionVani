
import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/services/session/session_service.dart';
import 'package:mobile_app/services/websocket/websocket_client.dart';
import 'package:mobile_app/services/websocket/websocket_message.dart';

class FakeWebSocketClient extends WebSocketClient {
  FakeWebSocketClient()
      : super(serverUrl: 'ws://127.0.0.1:8000/ws/session');

  bool connected = false;
  bool disposed = false;

  final List<WebSocketMessage> sentMessages = [];

  final StreamController<WebSocketMessage> _messagesController =
      StreamController<WebSocketMessage>.broadcast();

  final StreamController<WebSocketConnectionState>
      _connectionStatesController =
      StreamController<WebSocketConnectionState>.broadcast();

  @override
  bool get isConnected => connected;

  @override
  Stream<WebSocketMessage> get messages => _messagesController.stream;

  @override
  Stream<WebSocketConnectionState> get connectionStates =>
      _connectionStatesController.stream;

  @override
  Future<void> connect() async {
    connected = true;
    _connectionStatesController.add(
      WebSocketConnectionState.connected,
    );
  }

  @override
  void sendMessage(WebSocketMessage message) {
    if (!connected) {
      throw StateError('WebSocket is disconnected.');
    }

    sentMessages.add(message);
  }

  @override
  Future<void> disconnect() async {
    connected = false;
    _connectionStatesController.add(
      WebSocketConnectionState.disconnected,
    );
  }

  @override
  Future<void> dispose() async {
    await disconnect();
    disposed = true;
    await _messagesController.close();
    await _connectionStatesController.close();
  }
}

void main() {
  group('SessionService Tests', () {
    late FakeWebSocketClient fakeClient;
    late SessionService sessionService;

    setUp(() {
      fakeClient = FakeWebSocketClient();

      sessionService = SessionService(
        webSocketClient: fakeClient,
      );
    });

    tearDown(() async {
      await sessionService.dispose();
    });

    test('Initially has no active session', () {
      expect(sessionService.sessionId, isNull);
      expect(sessionService.isConnected, isFalse);
    });

    test('Starts a session and generates a session ID', () async {
      final sessionId = await sessionService.startSession();

      expect(sessionId, isNotEmpty);
      expect(sessionId, startsWith('session_'));
      expect(sessionService.sessionId, sessionId);
      expect(sessionService.isConnected, isTrue);
    });

    test('Starting an already connected session reuses its ID', () async {
      final firstSession = await sessionService.startSession();
      final secondSession = await sessionService.startSession();

      expect(secondSession, firstSession);
    });

    test('Generates unique request IDs', () async {
      await sessionService.startSession();

      final firstRequestId = sessionService.sendEvent(
        event: 'test.event',
        data: {'message': 'First message'},
      );

      final secondRequestId = sessionService.sendEvent(
        event: 'test.event',
        data: {'message': 'Second message'},
      );

      expect(firstRequestId, isNot(equals(secondRequestId)));
    });

    test('Sends the correct message through WebSocket client', () async {
      final sessionId = await sessionService.startSession();

      sessionService.sendEvent(
        event: 'test.connection',
        data: {'message': 'Hello ActionVani'},
      );

      expect(fakeClient.sentMessages, hasLength(1));

      final sentMessage = fakeClient.sentMessages.first;

      expect(sentMessage.event, 'test.connection');
      expect(sentMessage.sessionId, sessionId);
      expect(sentMessage.requestId, isNotEmpty);
      expect(sentMessage.data['message'], 'Hello ActionVani');
    });

    test('Cannot send an event while disconnected', () {
      expect(
        () => sessionService.sendEvent(
          event: 'test.event',
          data: {},
        ),
        throwsA(isA<StateError>()),
      );
    });

    test('Ends the session and disconnects the client', () async {
      await sessionService.startSession();

      await sessionService.endSession();

      expect(sessionService.sessionId, isNull);
      expect(sessionService.isConnected, isFalse);
    });

    test('Resets request counter when session ends', () async {
      await sessionService.startSession();

      final firstRequestId = sessionService.sendEvent(
        event: 'test.event',
        data: {},
      );

      await sessionService.endSession();
      await sessionService.startSession();

      final secondRequestId = sessionService.sendEvent(
        event: 'test.event',
        data: {},
      );

      expect(firstRequestId, isNot(secondRequestId));
      expect(secondRequestId, contains('request_1_'));
    });

    test('Cannot start a session after disposal', () async {
      await sessionService.dispose();

      expect(
        () => sessionService.startSession(),
        throwsA(isA<StateError>()),
      );
    });

    test('Cannot send events after disposal', () async {
      await sessionService.startSession();
      await sessionService.dispose();

      expect(
        () => sessionService.sendEvent(
          event: 'test.event',
          data: {},
        ),
        throwsA(isA<StateError>()),
      );
    });
  });
}
