
import 'package:flutter/material.dart';
import 'application_review_screen.dart';
import 'home_screen.dart';
import 'receipts_screen.dart';
import 'application_status_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() =>
      _MainNavigationScreenState();
}

class _MainNavigationScreenState
    extends State<MainNavigationScreen> {
  int _selectedIndex = 0;

  late final List<Widget> _screens = [
    ActionVaniHomeScreen(
      demoMode: true,
      onReceipts: () {
        setState(() {
          _selectedIndex = 1;
        });
      },
      onNewApplication: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) =>
            const ApplicationReviewScreen(),
          ),
        );
      },
    ),
    ReceiptsScreen(
      receipts: demoReceipts,
    ),
    const ApplicationStatusScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        backgroundColor: Colors.white,
        indicatorColor: const Color(0xFFA9C1CC),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.mic_none_rounded),
            selectedIcon: Icon(Icons.mic_rounded),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long_rounded),
            label: 'Receipts',
          ),
          NavigationDestination(
            icon: Icon(Icons.track_changes_outlined),
            selectedIcon: Icon(Icons.track_changes_rounded),
            label: 'Status',
          ),
        ],
      ),
    );
  }
}
