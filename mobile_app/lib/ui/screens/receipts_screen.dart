import 'package:material_ui/material_ui.dart';

class Receipt {
  final String applicationName;
  final String referenceNumber;
  final String submissionDate;

  const Receipt({
    required this.applicationName,
    required this.referenceNumber,
    required this.submissionDate,
  });
}

// Temporary demo data.
// Replace this with receipt data from Member 2 later.
const List<Receipt> demoReceipts = [
  Receipt(
    applicationName: 'Scholarship Application',
    referenceNumber: 'AV-2026-001',
    submissionDate: '12 November 2026',
  ),
  Receipt(
    applicationName: 'Income Certificate',
    referenceNumber: 'AV-2026-002',
    submissionDate: '10 November 2026',
  ),
  Receipt(
    applicationName: 'Caste Certificate',
    referenceNumber: 'AV-2026-003',
    submissionDate: '08 November 2026',
  ),
];

class ReceiptsScreen extends StatelessWidget {
  const ReceiptsScreen({super.key, this.receipts = demoReceipts});

  final List<Receipt> receipts;

  static const Color navy = Color(0xFF34495E);
  static const Color dustyBlue = Color(0xFF66869A);
  static const Color background = Color(0xFFEFF2F2);
  static const Color secondaryText = Color(0xFF5F6B7A);

  void _showMessage(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: background,
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: navy,
        elevation: 0,
        title: const Text(
          'My Receipts',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
      body: receipts.isEmpty
          ? _buildEmptyState()
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                const Text(
                  'Your application receipts',
                  style: TextStyle(
                    color: navy,
                    fontSize: 21,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'View and access your submitted application '
                  'acknowledgements here.',
                  style: TextStyle(
                    color: secondaryText,
                    fontSize: 14,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 22),

                ...receipts.map(
                  (receipt) => _buildReceiptCard(context, receipt),
                ),
              ],
            ),
    );
  }

  Widget _buildReceiptCard(BuildContext context, Receipt receipt) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFD8DEE3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: background,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.picture_as_pdf_outlined,
                  color: dustyBlue,
                  size: 27,
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      receipt.applicationName,
                      style: const TextStyle(
                        color: navy,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 7),
                    Text(
                      'Ref: ${receipt.referenceNumber}',
                      style: const TextStyle(
                        color: secondaryText,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      receipt.submissionDate,
                      style: const TextStyle(
                        color: secondaryText,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 18),
          const Divider(color: Color(0xFFD8DEE3)),
          const SizedBox(height: 8),

          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    _showMessage(
                      context,
                      'PDF opening will be connected later.',
                    );
                  },
                  icon: const Icon(Icons.open_in_new, size: 17),
                  label: const Text('Open PDF'),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                tooltip: 'Share receipt',
                onPressed: () {
                  _showMessage(
                    context,
                    'Receipt sharing will be connected later.',
                  );
                },
                icon: const Icon(Icons.share_outlined, color: dustyBlue),
              ),
              IconButton(
                tooltip: 'Print receipt',
                onPressed: () {
                  _showMessage(
                    context,
                    'Receipt printing will be connected later.',
                  );
                },
                icon: const Icon(Icons.print_outlined, color: dustyBlue),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(30),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.receipt_long_outlined, size: 70, color: dustyBlue),
            const SizedBox(height: 18),
            const Text(
              'No receipts yet',
              style: TextStyle(
                color: navy,
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Your application acknowledgement '
              'receipts will appear here after submission.',
              textAlign: TextAlign.center,
              style: TextStyle(color: secondaryText, fontSize: 14, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }
}
