
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/services/websocket/websocket_message.dart';

void main() {
  group('WebSocketMessage Tests', () {
    test('Valid message should encode into JSON correctly', () {
      final message = WebSocketMessage(
        event: 'session.start',
        sessionId: 'session_001',
        requestId: 'request_001',
        data: {'message': 'Hello ActionVani'},
      );

      expect(message.toJson(), {
        'event': 'session.start',
        'session_id': 'session_001',
        'request_id': 'request_001',
        'data': {'message': 'Hello ActionVani'},
      });
    });

    test('Valid JSON should decode correctly', () {
      const jsonMessage = '''
      {
        "event": "assistant.prompt",
        "session_id": "session_001",
        "request_id": "request_002",
        "data": {
          "message": "Please enter your district"
        }
      }
      ''';

      final message = WebSocketMessage.decode(jsonMessage);

      expect(message.event, 'assistant.prompt');
      expect(message.sessionId, 'session_001');
      expect(message.requestId, 'request_002');
      expect(
        message.data['message'],
        'Please enter your district',
      );
    });

    test('Missing fields should be rejected', () {
      expect(
        () => WebSocketMessage.fromJson({
          'event': 'session.start',
          'session_id': 'session_001',
        }),
        throwsA(isA<FormatException>()),
      );
    });

    test('Additional fields should be rejected', () {
      expect(
        () => WebSocketMessage.fromJson({
          'event': 'session.start',
          'session_id': 'session_001',
          'request_id': 'request_001',
          'data': {},
          'extra_field': 'unexpected',
        }),
        throwsA(isA<FormatException>()),
      );
    });

    test('Empty IDs should be rejected', () {
      expect(
        () => WebSocketMessage.fromJson({
          'event': 'session.start',
          'session_id': '',
          'request_id': '',
          'data': {},
        }),
        throwsA(isA<FormatException>()),
      );
    });
  });
}
