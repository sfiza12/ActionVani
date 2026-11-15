
import 'package:flutter/material.dart';

class ApplicationReviewScreen extends StatefulWidget {
  const ApplicationReviewScreen({super.key});

  @override
  State<ApplicationReviewScreen> createState() =>
      _ApplicationReviewScreenState();
}

class _ApplicationReviewScreenState
    extends State<ApplicationReviewScreen> {
  static const Color navy = Color(0xFF34495E);
  static const Color dustyBlue = Color(0xFF66869A);
  static const Color background = Color(0xFFEFF2F2);
  static const Color secondaryText = Color(0xFF5F6B7A);

  final Map<String, String> applicationDetails = {
    'Applicant Name': 'Demo User',
    'District': 'Bengaluru Urban',
    'State': 'Karnataka',
    'Application Type': 'Income Certificate',
    'Purpose': 'Education',
  };

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _editDetail(String label, String currentValue) async {
    final controller = TextEditingController(text: currentValue);

    final updatedValue = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text('Edit $label'),
          content: TextField(
            controller: controller,
            autofocus: true,
            decoration: InputDecoration(
              labelText: label,
              hintText: 'Enter $label',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(dialogContext);
              },
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                final value = controller.text.trim();

                if (value.isEmpty) {
                  return;
                }

                Navigator.pop(dialogContext, value);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: navy,
                foregroundColor: Colors.white,
              ),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    controller.dispose();

    if (updatedValue != null && mounted) {
      setState(() {
        applicationDetails[label] = updatedValue;
      });

      _showMessage('$label updated successfully.');
    }
  }

  void _confirmApplication() {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Confirm Application?'),
        content: const Text(
          'Please make sure all the information is correct. '
              'Do you want to proceed?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Go Back'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(dialogContext);

              _showMessage(
                'Confirmation received. '
                    'Submission will be connected later.',
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: navy,
              foregroundColor: Colors.white,
            ),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: background,
      appBar: AppBar(
        title: const Text(
          'Review Application',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        backgroundColor: Colors.white,
        foregroundColor: navy,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Review your details',
            style: TextStyle(
              color: navy,
              fontSize: 22,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Check the information below before confirming '
                'your application.',
            style: TextStyle(
              color: secondaryText,
              fontSize: 14,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 22),

          ...applicationDetails.entries.map(
                (entry) => _buildDetailCard(
              entry.key,
              entry.value,
            ),
          ),

          const SizedBox(height: 12),

          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFE4EDF1),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline, color: navy),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Please verify every detail carefully. '
                        'Your application should only be confirmed '
                        'when all information is correct.',
                    style: TextStyle(
                      color: navy,
                      fontSize: 13,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _confirmApplication,
              icon: const Icon(Icons.check_circle_outline),
              label: const Text('Confirm Application'),
              style: ElevatedButton.styleFrom(
                backgroundColor: navy,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),

          const SizedBox(height: 10),

          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () {
                Navigator.pop(context);
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: navy,
                padding: const EdgeInsets.symmetric(vertical: 15),
                side: const BorderSide(color: dustyBlue),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: const Text('Cancel'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailCard(String label, String value) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFFD8DEE3),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: secondaryText,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  value,
                  style: const TextStyle(
                    color: navy,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: 'Edit $label',
            onPressed: () => _editDetail(label, value),
            icon: const Icon(
              Icons.edit_outlined,
              color: dustyBlue,
            ),
          ),
        ],
      ),
    );
  }
}
