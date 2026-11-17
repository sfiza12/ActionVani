import 'package:material_ui/material_ui.dart';

class SummaryCard extends StatelessWidget {
  const SummaryCard({
    super.key,
    required this.label,
    required this.value,
    this.isRecognised = true,
    this.onEdit,
  });

  final String label;
  final String value;
  final bool isRecognised;
  final VoidCallback? onEdit;

  static const Color navy = Color(0xFF34495E);
  static const Color dustyBlue = Color(0xFF66869A);
  static const Color background = Color(0xFFEFF2F2);
  static const Color secondaryText = Color(0xFF5F6B7A);
  static const Color border = Color(0xFFD8DEE3);
  static const Color success = Color(0xFF2E7D32);

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      label: '$label: $value',
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Field label and recognition status.
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Text(
                    label.toUpperCase(),
                    style: const TextStyle(
                      color: secondaryText,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
                if (isRecognised)
                  const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.check_circle_rounded,
                        color: success,
                        size: 16,
                      ),
                      SizedBox(width: 5),
                      Text(
                        'Recognised',
                        style: TextStyle(
                          color: success,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  )
                else
                  const Text(
                    'Needs review',
                    style: TextStyle(
                      color: Color(0xFFE7A23C),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
              ],
            ),

            const SizedBox(height: 10),

            // Recognised information.
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Text(
                    value.isEmpty ? 'Not provided' : value,
                    style: const TextStyle(
                      color: Color(0xFF1F2A37),
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                      height: 1.4,
                    ),
                    softWrap: true,
                  ),
                ),

                if (onEdit != null) ...[
                  const SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Edit $label',
                    onPressed: onEdit,
                    icon: const Icon(Icons.edit_outlined, color: dustyBlue),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}
