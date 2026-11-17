import 'package:material_ui/material_ui.dart';

Future<String?> showActionVaniCaptchaDialog(BuildContext context) {
  return showDialog<String>(
    context: context,
    barrierDismissible: false,
    builder: (context) => const CaptchaDialog(),
  );
}

class CaptchaDialog extends StatefulWidget {
  const CaptchaDialog({super.key});

  @override
  State<CaptchaDialog> createState() => _CaptchaDialogState();
}

class _CaptchaDialogState extends State<CaptchaDialog> {
  final TextEditingController _captchaController = TextEditingController();

  static const Color navy = Color(0xFF34495E);
  static const Color dustyBlue = Color(0xFF66869A);

  void _confirmCaptcha() {
    final answer = _captchaController.text.trim();

    if (answer.isEmpty) {
      return;
    }

    _captchaController.clear();
    Navigator.of(context).pop(answer);
  }

  void _cancelCaptcha() {
    _captchaController.clear();
    Navigator.of(context).pop();
  }

  @override
  void dispose() {
    _captchaController.clear();
    _captchaController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      title: const Row(
        children: [
          Icon(Icons.verified_user_outlined, color: navy),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'CAPTCHA Verification',
              style: TextStyle(
                color: navy,
                fontSize: 19,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Please complete the verification challenge '
              'to continue.',
              style: TextStyle(
                color: Color(0xFF5F6B7A),
                fontSize: 14,
                height: 1.5,
              ),
            ),

            const SizedBox(height: 20),

            // Temporary placeholder for the CAPTCHA image.
            // Replace this with the image supplied by the service.
            Container(
              width: double.infinity,
              height: 100,
              decoration: BoxDecoration(
                color: const Color(0xFFEFF2F2),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFD8DEE3)),
              ),
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.image_outlined, size: 30, color: dustyBlue),
                    SizedBox(height: 6),
                    Text(
                      'CAPTCHA image will appear here',
                      style: TextStyle(color: Color(0xFF5F6B7A), fontSize: 12),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            const Text(
              'Enter the characters shown in the image',
              style: TextStyle(
                color: navy,
                fontWeight: FontWeight.w600,
                fontSize: 14,
              ),
            ),

            const SizedBox(height: 10),

            TextField(
              controller: _captchaController,
              autofocus: true,
              textCapitalization: TextCapitalization.characters,
              decoration: InputDecoration(
                hintText: 'Enter CAPTCHA',
                prefixIcon: const Icon(
                  Icons.keyboard_outlined,
                  color: dustyBlue,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(color: dustyBlue, width: 2),
                ),
              ),
              onSubmitted: (_) => _confirmCaptcha(),
            ),
          ],
        ),
      ),
      actionsPadding: const EdgeInsets.fromLTRB(20, 0, 20, 18),
      actions: [
        TextButton(
          onPressed: _cancelCaptcha,
          child: const Text(
            'Cancel',
            style: TextStyle(color: Color(0xFF5F6B7A)),
          ),
        ),
        ElevatedButton(
          onPressed: _confirmCaptcha,
          style: ElevatedButton.styleFrom(
            backgroundColor: navy,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: const Text('Confirm'),
        ),
      ],
    );
  }
}
