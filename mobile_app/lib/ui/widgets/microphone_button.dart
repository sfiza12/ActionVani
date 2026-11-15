import 'package:flutter/material.dart';

class MicrophoneButton extends StatefulWidget {
  const MicrophoneButton({
    super.key,
    required this.isListening,
    required this.isProcessing,
    required this.hasError,
    required this.isResponseReceived,
    required this.onTap,
  });

  final bool isListening;
  final bool isProcessing;
  final bool hasError;
  final bool isResponseReceived;
  final VoidCallback onTap;

  static const Color navy = Color(0xFF34495E);
  static const Color paleBlue = Color(0xFFA9C1CC);
  static const Color successGreen = Color(0xFF2E7D32);
  static const Color errorRed = Color(0xFFC34D48);

  @override
  State<MicrophoneButton> createState() => _MicrophoneButtonState();
}

class _MicrophoneButtonState extends State<MicrophoneButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;

  @override
  void initState() {
    super.initState();

    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    );

    _updateAnimation();
  }

  @override
  void didUpdateWidget(covariant MicrophoneButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    _updateAnimation();
  }

  void _updateAnimation() {
    if (widget.isListening) {
      if (!_pulse.isAnimating) {
        _pulse.repeat(reverse: true);
      }
    } else {
      _pulse.stop();
      _pulse.value = 0;
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 154,
      height: 154,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Fixed-size pulsing outer ring.
          AnimatedBuilder(
            animation: _pulse,
            builder: (context, child) {
              return Container(
                width: 142,
                height: 142,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: MicrophoneButton.paleBlue.withValues(
                    alpha: widget.isListening
                        ? 0.12 + (0.10 * _pulse.value)
                        : 0.18,
                  ),
                ),
              );
            },
          ),

          // Main microphone button.
          Semantics(
            button: true,
            label: widget.isListening
                ? 'Stop recording'
                : widget.isProcessing
                ? 'Processing voice'
                : widget.isResponseReceived
                ? 'Recording successful'
                : widget.hasError
                ? 'Recording error'
                : 'Start voice recording',
            child: Material(
              color: widget.hasError
                  ? MicrophoneButton.errorRed
                  : widget.isResponseReceived
                  ? MicrophoneButton.successGreen
                  : MicrophoneButton.navy,
              shape: const CircleBorder(),
              elevation: 5,
              shadowColor: MicrophoneButton.navy.withValues(alpha: 0.22),
              child: InkWell(
                customBorder: const CircleBorder(),
                onTap: widget.isProcessing ? null : widget.onTap,
                child: SizedBox(
                  width: 116,
                  height: 116,
                  child: Center(
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 250),
                      transitionBuilder: (child, animation) {
                        return ScaleTransition(
                          scale: animation,
                          child: FadeTransition(
                            opacity: animation,
                            child: child,
                          ),
                        );
                      },
                      child: _buildButtonIcon(),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildButtonIcon() {
    if (widget.isProcessing) {
      return const SizedBox(
        key: ValueKey('processing'),
        width: 36,
        height: 36,
        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 3),
      );
    }

    if (widget.hasError) {
      return const Icon(
        Icons.error_outline_rounded,
        key: ValueKey('error'),
        color: Colors.white,
        size: 52,
      );
    }

    if (widget.isResponseReceived) {
      return const Icon(
        Icons.check_rounded,
        key: ValueKey('success'),
        color: Colors.white,
        size: 56,
      );
    }

    if (widget.isListening) {
      return const Icon(
        Icons.graphic_eq_rounded,
        key: ValueKey('listening'),
        color: Colors.white,
        size: 52,
      );
    }

    return const Icon(
      Icons.mic_none_rounded,
      key: ValueKey('idle'),
      color: Colors.white,
      size: 52,
    );
  }
}
