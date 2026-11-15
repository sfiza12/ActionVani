
import 'package:flutter/material.dart';
import 'ui/screens/main_navigation_screen.dart';

void main() {
  runApp(const ActionVaniApp());
}

class ActionVaniApp extends StatelessWidget {
  const ActionVaniApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ActionVani',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF66869A),
        ),
      ),
      home: const MainNavigationScreen(),
    );
  }
}
