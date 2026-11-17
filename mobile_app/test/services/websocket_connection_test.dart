
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/services/websocket/websocket_client.dart';
import 'package:mobile_app/services/websocket/websocket_message.dart';

void main() {
  test(
    'Connect to ActionVani backend and receive echoed message',
    () async {
      final client = WebSocketClient(
        serverUrl: 'ws://127.0.0.1:8000/ws/session',
      );

      try {
        final responseFuture = client.messages.first.timeout(
          const Duration(seconds: 10),
        );

        await client.connect();

        client.sendMessage(
  WebSocketMessage(
    event: 'test.connection',
    sessionId: 'actionvani-test-session',
    requestId: 'request-001',
    data: {
      'message': 'Hello from ActionVani Flutter!',
    },
  ),
);

        final response = await responseFuture;

        expect(response.event, 'test.connection');
        expect(response.sessionId, 'actionvani-test-session');
        expect(response.requestId, 'request-001');
        expect(
          response.data['message'],
          'Hello from ActionVani Flutter!',
        );
      } finally {
        await client.dispose();
      }
    },
    timeout: const Timeout(Duration(seconds: 20)),
  );
}
