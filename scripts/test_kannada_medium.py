
import time
from pathlib import Path

import torch
import soundfile as sf

from transformers import (
    AutoProcessor,
    AutoModelForSpeechSeq2Seq,
)


# ==========================================
# 1. CONFIGURATION
# ==========================================

MODEL_ID = "vasista22/whisper-kannada-medium"

ROOT = Path(__file__).resolve().parents[1]

AUDIO_PATH = (
    ROOT
    / "datasets"
    / "processed_audio"
    / "kannada"
    / "kannada_test.wav"
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

DTYPE = (
    torch.float16
    if DEVICE == "cuda"
    else torch.float32
)


# ==========================================
# 2. GPU INITIALIZATION
# ==========================================

print("=" * 55)
print("ACTIONVANI KANNADA SPEECH RECOGNITION")
print("=" * 55)

print("Device:", DEVICE)

if DEVICE == "cuda":

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    print("GPU:", torch.cuda.get_device_name(0))


# ==========================================
# 3. LOAD PROCESSOR
# ==========================================

print("\nLoading Kannada processor...")

processor = AutoProcessor.from_pretrained(
    MODEL_ID
)


# ==========================================
# 4. LOAD MODEL
# ==========================================

print("\nLoading Kannada Whisper Medium model...")

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_ID,
    dtype=DTYPE,
    low_cpu_mem_usage=True,
)

model = model.to(DEVICE)

model.eval()

print("Model loaded successfully!")


# ==========================================
# 5. VALIDATE AUDIO
# ==========================================

print("\nChecking audio file...")

if not AUDIO_PATH.exists():
    raise FileNotFoundError(
        f"Audio file not found: {AUDIO_PATH}"
    )

audio, sample_rate = sf.read(AUDIO_PATH)

if audio.size == 0:
    raise ValueError("Audio file is empty.")

if audio.ndim > 1:
    audio = audio.mean(axis=1)

if sample_rate != 16000:
    raise ValueError(
        f"Expected 16000 Hz audio, received {sample_rate} Hz."
    )

duration = len(audio) / sample_rate

print("Audio file:", AUDIO_PATH.name)
print("Sample rate:", sample_rate)
print("Duration:", round(duration, 2), "seconds")


# ==========================================
# 6. PREPARE AUDIO FEATURES
# ==========================================

print("\nPreparing audio features...")

inputs = processor(
    audio,
    sampling_rate=sample_rate,
    return_tensors="pt",
)

features = inputs.input_features.to(
    device=DEVICE,
    dtype=DTYPE,
)


# ==========================================
# 7. CONFIGURE KANNADA DECODING
# ==========================================

print("\nConfiguring Kannada transcription...")

model.config.forced_decoder_ids = (
    processor.get_decoder_prompt_ids(
        language="kn",
        task="transcribe",
    )
)

# Avoid conflicting max_length and max_new_tokens.
model.generation_config.max_length = 128


# ==========================================
# 8. TRANSCRIBE AUDIO
# ==========================================

print("\nTranscribing Kannada...")

start_time = time.perf_counter()

with torch.inference_mode():

    generated_ids = model.generate(
        features,
        num_beams=5,
    )

processing_time = time.perf_counter() - start_time


# ==========================================
# 9. DECODE TRANSCRIPTION
# ==========================================

transcription = processor.batch_decode(
    generated_ids,
    skip_special_tokens=True,
    clean_up_tokenization_spaces=False,
)[0]

transcription = transcription.strip()


# ==========================================
# 10. DISPLAY RESULTS
# ==========================================

print("\n" + "=" * 55)
print("KANNADA TRANSCRIPTION")
print("=" * 55)

print(transcription)

print("\nProcessing time:",
      round(processing_time, 2), "seconds")


# ==========================================
# 11. GPU MEMORY
# ==========================================

if DEVICE == "cuda":

    allocated = (
        torch.cuda.memory_allocated(0) / 1024**3
    )

    peak = (
        torch.cuda.max_memory_allocated(0) / 1024**3
    )

    print("\nGPU memory allocated:",
          round(allocated, 2), "GB")

    print("Peak GPU memory:",
          round(peak, 2), "GB")


# ==========================================
# 12. SAVE TRANSCRIPTION
# ==========================================

OUTPUT_DIR = (
    ROOT
    / "datasets"
    / "evaluation"
    / "speech"
    / "whisper_kannada_medium"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE = OUTPUT_DIR / "kannada_medium_result.txt"

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:

    file.write(transcription)

print("\nSaved transcription to:")
print(OUTPUT_FILE)

print("\n" + "=" * 55)
print("KANNADA TEST COMPLETED")
print("=" * 55)
