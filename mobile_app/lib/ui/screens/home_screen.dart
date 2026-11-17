import 'package:material_ui/material_ui.dart';
import '../widgets/summary_card.dart';
import '../widgets/microphone_button.dart';
import '../widgets/recording_indicator.dart';

/// ActionVani home screen.
/// All sample conversations are DEMO DATA.
///
/// Replace demoMode with false and provide callbacks/state
/// from Member 2 when the service interfaces are ready.

enum VoiceUiState { idle, listening, processing, responseReceived, error }

class VoiceMessage {
  const VoiceMessage({required this.text, required this.fromAssistant});

  final String text;
  final bool fromAssistant;
}

class CapturedField {
  const CapturedField({required this.label, required this.value});

  final String label;
  final String value;
}

class ActionVaniHomeScreen extends StatefulWidget {
  const ActionVaniHomeScreen({
    super.key,
    this.demoMode = true,
    this.voiceState = VoiceUiState.idle,
    this.messages = const [],
    this.capturedFields = const [],
    this.onStartRecording,
    this.onStopRecording,
    this.onNewApplication,
    this.onReceipts,
    this.onHelp,
    this.onLanguageChanged,
  });

  /// Set to false when connecting Member 2's service interfaces.
  final bool demoMode;

  final VoiceUiState voiceState;
  final List<VoiceMessage> messages;
  final List<CapturedField> capturedFields;

  final VoidCallback? onStartRecording;
  final VoidCallback? onStopRecording;
  final VoidCallback? onNewApplication;
  final VoidCallback? onReceipts;
  final VoidCallback? onHelp;

  final ValueChanged<String>? onLanguageChanged;

  @override
  State<ActionVaniHomeScreen> createState() => _ActionVaniHomeScreenState();
}

class _ActionVaniHomeScreenState extends State<ActionVaniHomeScreen> {
  static const _navy = Color(0xFF34495E);
  static const _dustyBlue = Color(0xFF66869A);
  static const _canvas = Color(0xFFEFF2F2);
  static const _ink = Color(0xFF1F2A37);
  static const _muted = Color(0xFF5F6B7A);
  static const _border = Color(0xFFD8DEE3);

  late VoiceUiState _demoState;

  String _language = 'English';
  int _demoRequest = 0;

  final List<VoiceMessage> _demoMessages = [
    const VoiceMessage(
      text: 'Hello! I can help you fill out an application. Tap the microphone to begin.',
      fromAssistant: true,
    ),
  ];

  final List<CapturedField> _demoFields = [];

  VoiceUiState get _state => widget.demoMode ? _demoState : widget.voiceState;

  List<VoiceMessage> get _messages =>
      widget.demoMode ? _demoMessages : widget.messages;

  List<CapturedField> get _fields =>
      widget.demoMode ? _demoFields : widget.capturedFields;

  @override
  void initState() {
    super.initState();
    _demoState = widget.voiceState;
  }

  @override
  void didUpdateWidget(covariant ActionVaniHomeScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.voiceState != widget.voiceState && !widget.demoMode) {
      // The live state is supplied by the parent when integrated.
    }
  }

  @override
  void dispose() {
    _demoRequest++;
    super.dispose();
  }

  void _setDemoState(VoiceUiState state) {
    if (!mounted) return;

    setState(() {
      _demoState = state;
    });
  }


  Future<void> _handleMicrophone() async {
    // Live mode: delegate recording actions to Member 2's service.
    if (!widget.demoMode) {
      if (_state == VoiceUiState.listening) {
        widget.onStopRecording?.call();
      } else if (_state != VoiceUiState.processing) {
        widget.onStartRecording?.call();
      }

      return;
    }

    // Do not allow another action while processing.
    if (_state == VoiceUiState.processing) return;

    // First tap: enter listening state.
    if (_state != VoiceUiState.listening) {
      _demoRequest++;
      _setDemoState(VoiceUiState.listening);
      return;
    }

    // Second tap: simulate processing.
    final request = ++_demoRequest;

    _setDemoState(VoiceUiState.processing);

    // Simulate voice processing.
    await Future<void>.delayed(
      const Duration(milliseconds: 900),
    );

    if (!mounted || request != _demoRequest) return;

    // Add demo conversation and captured information.
    setState(() {
      _demoMessages.addAll(const [
        VoiceMessage(
          text: 'My district is Bengaluru Urban.',
          fromAssistant: false,
        ),
        VoiceMessage(
          text:
          'Thanks! I understood your district as Bengaluru Urban. Is that correct?',
          fromAssistant: true,
        ),
      ]);

      _demoFields.removeWhere(
            (field) => field.label == 'District',
      );

      _demoFields.add(
        const CapturedField(
          label: 'District',
          value: 'Bengaluru Urban',
        ),
      );
    });

    // Display the green success tick.
    _setDemoState(VoiceUiState.responseReceived);

    // Keep the success tick visible for 1.5 seconds.
    await Future<void>.delayed(
      const Duration(milliseconds: 1500),
    );

    // Avoid resetting if the widget was disposed or a new request started.
    if (!mounted || request != _demoRequest) return;

    // Return to the idle microphone.
    if (_demoState == VoiceUiState.responseReceived) {
      _setDemoState(VoiceUiState.idle);
    }
  }


  void _showDemoNotice(String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$feature will open when navigation is connected.'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final status = switch (_state) {
      VoiceUiState.idle => 'Tap to speak',
      VoiceUiState.listening => 'Listening to you…',
      VoiceUiState.processing => 'Understanding your answer…',
      VoiceUiState.responseReceived => 'Answer received',
      VoiceUiState.error => 'Something went wrong',
    };

    final hint = switch (_state) {
      VoiceUiState.idle => 'Speak naturally. We’ll guide you step by step.',
      VoiceUiState.listening => 'Tap again when you are finished speaking.',
      VoiceUiState.processing => 'Please wait a moment.',
      VoiceUiState.responseReceived =>
        'Review the information below or speak again.',
      VoiceUiState.error => 'Please try again.',
    };

    return Scaffold(
      backgroundColor: _canvas,
      appBar: AppBar(
        backgroundColor: _canvas,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        titleSpacing: 20,
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.graphic_eq_rounded, color: _navy, size: 30),
            SizedBox(width: 8),
            Text(
              'Action',
              style: TextStyle(fontWeight: FontWeight.w800, color: _ink),
            ),
            Text(
              'Vani',
              style: TextStyle(fontWeight: FontWeight.w800, color: _dustyBlue),
            ),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            tooltip: 'Choose language',
            initialValue: _language,
            onSelected: (value) {
              setState(() {
                _language = value;
              });

              widget.onLanguageChanged?.call(value);
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'English', child: Text('English')),
              PopupMenuItem(value: 'हिन्दी', child: Text('हिन्दी')),
              PopupMenuItem(value: 'ಕನ್ನಡ', child: Text('ಕನ್ನಡ')),
            ],
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  const Icon(Icons.language_rounded, color: _navy),
                  const SizedBox(width: 5),
                  Text(
                    _language,
                    style: const TextStyle(color: _navy, fontSize: 13),
                  ),
                  const Icon(Icons.arrow_drop_down, color: _navy),
                ],
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
              children: [
                if (widget.demoMode)
                  const Padding(
                    padding: EdgeInsets.only(bottom: 12),
                    child: Text(
                      'DEMO PREVIEW · Sample data only',
                      style: TextStyle(
                        color: _muted,
                        fontSize: 11,
                        letterSpacing: 1.2,
                      ),
                    ),
                  ),

                // Welcome heading
                const Text(
                  'Forms made simple.',
                  style: TextStyle(
                    color: _ink,
                    fontSize: 30,
                    fontWeight: FontWeight.w800,
                    height: 1.12,
                    letterSpacing: -0.7,
                  ),
                ),

                const SizedBox(height: 8),

                const Text(
                  'Just speak, and ActionVani will help you complete your application.',
                  style: TextStyle(color: _muted, fontSize: 16, height: 1.5),
                ),

                const SizedBox(height: 22),

                // Voice assistant card
                Container(
                  padding: const EdgeInsets.symmetric(
                    vertical: 30,
                    horizontal: 18,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(26),
                    border: Border.all(color: _border),
                  ),
                  child: Column(
                    children: [
                      const Text(
                        'YOUR VOICE ASSISTANT',
                        style: TextStyle(
                          color: _muted,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.3,
                        ),
                      ),

                      const SizedBox(height: 26),

                      // Reusable microphone widget
                      MicrophoneButton(
                        isListening: _state == VoiceUiState.listening,
                        isProcessing: _state == VoiceUiState.processing,
                        hasError: _state == VoiceUiState.error,
                        isResponseReceived:
                            _state == VoiceUiState.responseReceived,
                        onTap: _handleMicrophone,
                      ),

                      const SizedBox(height: 16),

                      Text(
                        status,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: _ink,
                          fontSize: 21,
                          fontWeight: FontWeight.w700,
                        ),
                      ),

                      const SizedBox(height: 6),

                      Text(
                        hint,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: _muted,
                          fontSize: 14,
                          height: 1.4,
                        ),
                      ),

                      if (_state == VoiceUiState.listening) ...[
                        const SizedBox(height: 16),
                        const RecordingIndicator(),
                      ],
                    ], // Close voice assistant Column children
                  ), // Close voice assistant Column
                ), // Close voice assistant Container

                const SizedBox(height: 22),

                // Shortcut buttons
                const SizedBox(height: 22),

                // Shortcut buttons
                Row(
                  children: [
                    Expanded(
                      child: _ShortcutTile(
                        icon: Icons.note_add_outlined,
                        label: 'New\nApplication',
                        onTap:
                            widget.onNewApplication ??
                            () => _showDemoNotice('New Application'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _ShortcutTile(
                        icon: Icons.receipt_long_outlined,
                        label: 'My\nReceipts',
                        onTap:
                            widget.onReceipts ??
                            () => _showDemoNotice('My Receipts'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _ShortcutTile(
                        icon: Icons.help_outline_rounded,
                        label: 'Help',
                        onTap: widget.onHelp ?? () => _showDemoNotice('Help'),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 28),

                // Conversation section
                _sectionTitle('Conversation', Icons.forum_outlined),

                const SizedBox(height: 12),

                if (_messages.isEmpty)
                  const _EmptyPanel(
                    icon: Icons.chat_bubble_outline_rounded,
                    text: 'Your conversation will appear here.',
                  )
                else
                  ..._messages.map(
                    (message) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Align(
                        alignment: message.fromAssistant
                            ? Alignment.centerLeft
                            : Alignment.centerRight,
                        child: Container(
                          constraints: const BoxConstraints(maxWidth: 440),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: message.fromAssistant
                                ? Colors.white
                                : const Color(0xFFDDE8ED),
                            borderRadius: BorderRadius.circular(18),
                            border: Border.all(color: _border),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                message.fromAssistant ? 'ActionVani' : 'You',
                                style: const TextStyle(
                                  color: _navy,
                                  fontWeight: FontWeight.w700,
                                  fontSize: 12,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                message.text,
                                style: const TextStyle(
                                  color: _ink,
                                  fontSize: 15,
                                  height: 1.45,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),

                const SizedBox(height: 20),

                // Captured information section

                // Captured information section
                _sectionTitle(
                  'Information understood',
                  Icons.fact_check_outlined,
                ),

                const SizedBox(height: 12),

                if (_fields.isEmpty)
                  const _EmptyPanel(
                    icon: Icons.assignment_outlined,
                    text:
                    'Information you share will be shown here for review.',
                  )
                else
                  ..._fields.map(
                        (field) => SummaryCard(
                      label: field.label,
                      value: field.value,
                      isRecognised: true,
                    ),
                  ),

                const SizedBox(height: 20),


                // Password safety reminder
                const Row(
                  children: [
                    Icon(Icons.lock_outline, size: 17, color: _muted),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Never speak your password or OTP aloud.',
                        style: TextStyle(color: _muted, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _sectionTitle(String text, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: _navy, size: 21),
        const SizedBox(width: 9),
        Text(
          text,
          style: const TextStyle(
            color: _ink,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

class _ShortcutTile extends StatelessWidget {
  const _ShortcutTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Container(
          constraints: const BoxConstraints(minHeight: 112),
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 5),
          decoration: BoxDecoration(
            border: Border.all(color: const Color(0xFFD8DEE3)),
            borderRadius: BorderRadius.circular(18),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 29, color: const Color(0xFF34495E)),
              const SizedBox(height: 10),
              Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Color(0xFF1F2A37),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  height: 1.2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyPanel extends StatelessWidget {
  const _EmptyPanel({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFD8DEE3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: const Color(0xFF66869A), size: 30),
          const SizedBox(height: 9),
          Text(
            text,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Color(0xFF5F6B7A), fontSize: 14),
          ),
        ],
      ),
    );
  }
}
