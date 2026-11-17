import 'package:material_ui/material_ui.dart';

Future<String?> showActionVaniPasswordDialog(BuildContext context) {
  return showDialog<String>(
    context: context,
    barrierDismissible: false,
    builder: (context) => const PasswordDialog(),
  );
}

class PasswordDialog extends StatefulWidget {
  const PasswordDialog({super.key});

  @override
  State<PasswordDialog> createState() => _PasswordDialogState();
}

class _PasswordDialogState extends State<PasswordDialog> {
  final TextEditingController _passwordController = TextEditingController();

  bool _obscurePassword = true;

  static const Color navy = Color(0xFF34495E);
  static const Color dustyBlue = Color(0xFF66869A);

  void _submitPassword() {
    final password = _passwordController.text;

    if (password.trim().isEmpty) {
      return;
    }

    _passwordController.clear();
    Navigator.of(context).pop(password);
  }

  void _cancelDialog() {
    _passwordController.clear();
    Navigator.of(context).pop();
  }

  @override
  void dispose() {
    _passwordController.clear();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      title: const Row(
        children: [
          Icon(Icons.lock_outline_rounded, color: navy),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Secure Password Entry',
              style: TextStyle(
                color: navy,
                fontSize: 19,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Enter your password using the keyboard. '
            'Password input is never requested through voice.',
            style: TextStyle(
              color: Color(0xFF5F6B7A),
              fontSize: 14,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 20),
          TextField(
            controller: _passwordController,
            obscureText: _obscurePassword,
            autofocus: true,
            decoration: InputDecoration(
              labelText: 'Password',
              hintText: 'Enter your password',
              prefixIcon: const Icon(Icons.lock_outline, color: dustyBlue),
              suffixIcon: IconButton(
                tooltip: _obscurePassword ? 'Show password' : 'Hide password',
                icon: Icon(
                  _obscurePassword
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                ),
                onPressed: () {
                  setState(() {
                    _obscurePassword = !_obscurePassword;
                  });
                },
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: const BorderSide(color: dustyBlue, width: 2),
              ),
            ),
            onSubmitted: (_) => _submitPassword(),
          ),
        ],
      ),
      actionsPadding: const EdgeInsets.fromLTRB(20, 0, 20, 18),
      actions: [
        TextButton(
          onPressed: _cancelDialog,
          child: const Text(
            'Cancel',
            style: TextStyle(color: Color(0xFF5F6B7A)),
          ),
        ),
        ElevatedButton(
          onPressed: _submitPassword,
          style: ElevatedButton.styleFrom(
            backgroundColor: navy,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: const Text('Submit'),
        ),
      ],
    );
  }
}
