import 'package:flutter/material.dart';

enum ApplicationStage { submitted, processing, verification, completed }

class ApplicationStatusScreen extends StatelessWidget {
  const ApplicationStatusScreen({
    super.key,
    this.referenceNumber = 'AV-DEMO-2026-001',
    this.currentStage = ApplicationStage.processing,
    this.statusMessage = 'Your application is being processed.',
    this.isLoading = false,
    this.errorMessage,
  });

  final String? referenceNumber;
  final ApplicationStage currentStage;
  final String statusMessage;
  final bool isLoading;
  final String? errorMessage;

  static const Color navy = Color(0xFF34495E);
  static const Color dustyBlue = Color(0xFF66869A);
  static const Color background = Color(0xFFEFF2F2);
  static const Color secondaryText = Color(0xFF5F6B7A);
  static const Color success = Color(0xFF2E7D32);

  static const List<String> stages = [
    'Application Submitted',
    'Processing',
    'Verification',
    'Completed',
  ];

  @override
  Widget build(BuildContext context) {
    final currentIndex = currentStage.index;

    return Scaffold(
      backgroundColor: background,
      appBar: AppBar(
        title: const Text(
          'Application Status',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        backgroundColor: Colors.white,
        foregroundColor: navy,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Track your application',
              style: TextStyle(
                color: navy,
                fontSize: 22,
                fontWeight: FontWeight.w700,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              'Check the latest progress of your application.',
              style: TextStyle(color: secondaryText, fontSize: 14),
            ),

            const SizedBox(height: 22),

            _buildReferenceCard(),

            const SizedBox(height: 20),

            if (isLoading)
              _buildLoading()
            else if (errorMessage != null)
              _buildError(errorMessage!)
            else ...[
              _buildStatusCard(),
              const SizedBox(height: 22),
              const Text(
                'Application Progress',
                style: TextStyle(
                  color: navy,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 18),
              ...List.generate(
                stages.length,
                (index) => _buildStageItem(index, currentIndex),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildReferenceCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFD8DEE3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'APPLICATION REFERENCE',
            style: TextStyle(
              color: secondaryText,
              fontSize: 12,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.7,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            referenceNumber ?? 'Not available yet',
            style: const TextStyle(
              color: navy,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFE4EDF1),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline, color: navy, size: 25),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              statusMessage,
              style: const TextStyle(
                color: navy,
                fontSize: 14,
                height: 1.5,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStageItem(int index, int currentIndex) {
    final isCompleted = index < currentIndex;
    final isCurrent = index == currentIndex;

    final Color stageColor = isCompleted
        ? success
        : isCurrent
        ? dustyBlue
        : const Color(0xFFB0BAC2);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 34,
            child: Column(
              children: [
                CircleAvatar(
                  radius: 15,
                  backgroundColor: stageColor,
                  child: Icon(
                    isCompleted
                        ? Icons.check
                        : isCurrent
                        ? Icons.more_horiz
                        : Icons.circle_outlined,
                    color: Colors.white,
                    size: 17,
                  ),
                ),
                if (index != stages.length - 1)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: isCompleted ? success : const Color(0xFFD8DEE3),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 25, top: 5),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    stages[index],
                    style: TextStyle(
                      color: stageColor,
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    isCompleted
                        ? 'Stage completed'
                        : isCurrent
                        ? 'Current stage'
                        : 'Pending',
                    style: const TextStyle(color: secondaryText, fontSize: 13),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoading() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(35),
        child: Column(
          children: [
            CircularProgressIndicator(color: dustyBlue),
            SizedBox(height: 16),
            Text(
              'Loading application status...',
              style: TextStyle(color: secondaryText),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError(String message) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFFFEEEE),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFD94B3D), size: 35),
          const SizedBox(height: 10),
          const Text(
            'Unable to load status',
            style: TextStyle(
              color: navy,
              fontWeight: FontWeight.w700,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: secondaryText, fontSize: 14),
          ),
        ],
      ),
    );
  }
}
