
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/main.dart';

void main() {
  testWidgets('ActionVani app launches', (WidgetTester tester) async {
    await tester.pumpWidget(const ActionVaniApp());

    expect(find.byType(ActionVaniApp), findsOneWidget);
  });
}
