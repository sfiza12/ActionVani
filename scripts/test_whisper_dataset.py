
import json
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
import soundfile as sf
import torch

from transformers import (
    AutoProcessor,
    AutoModelForSpeechSeq2Seq,
)

# ---------------------------------
# 1. Project paths and configuration
# ---------------------------------

ROOT = Path(__file__).resolve().parents[1]

MODEL_ID = "openai/whisper-small"

DATASETS = [
    {
        "language": "english",
        "whisper_language": "english",
        "input": ROOT / "datasets/audio/english/eng_audio.mp4",
    },
    {
        "language": "hindi",
        "whisper_language": "hindi",
        "input": ROOT / "datasets/audio/hindi/hin_audio.mp4",
    },
    {
        "language": "kannada",
        "whisper_language": "kannada",
        "input": ROOT / "datasets/audio/kannada/kan_audio.mp4",
    },
]

OUTPUT_DIR = ROOT / "datasets/processed_audio"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

SAMPLE_RATE = 16000

# ---------------------------------
# 2. Convert MP4 into WAV
# ---------------------------------

def convert_to_wav(input_path, output_path):

    if not input_path.exists():
        raise FileNotFoundError(f"Audio not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg,
        "-y",
        "-i", str(input_path),
        "-vn",
        "-ac", "1",
        "-ar", str(SAMPLE_RATE),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    print(f"Converted: {output_path.name}")

# ---------------------------------
# 3. Load Whisper
# ---------------------------------

def load_whisper():

    print("\nLoading Whisper processor...")

    processor = AutoProcessor.from_pretrained(MODEL_ID)

    print("Loading Whisper model...")

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        MODEL_ID,
        dtype=DTYPE,
        low_cpu_mem_usage=True,
    )

    model = model.to(DEVICE)
    model.eval()

    print("Whisper ready!")
    print("Device:", DEVICE)

    if DEVICE == "cuda":
        print("GPU:", torch.cuda.get_device_name(0))

    return processor, model

# ---------------------------------
# 4. Transcribe audio
# ---------------------------------

def transcribe_audio(processor, model, wav_path, language):

    audio, sample_rate = sf.read(wav_path)

    if audio.size == 0:
        raise ValueError("Audio file is empty")

    inputs = processor(
        audio,
        sampling_rate=sample_rate,
        return_tensors="pt",
    )

    input_features = inputs.input_features.to(
        device=DEVICE,
        dtype=DTYPE,
    )

    forced_decoder_ids = processor.get_decoder_prompt_ids(
        language=language,
        task="transcribe",
    )

    start = time.perf_counter()

    with torch.inference_mode():

        generated_ids = model.generate(
            input_features,
            forced_decoder_ids=forced_decoder_ids,
        )

    elapsed = time.perf_counter() - start

    transcription = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True,
    )[0]

    return transcription.strip(), round(elapsed, 2)

# ---------------------------------
# 5. Main execution
# ---------------------------------

def main():

    print("=" * 55)
    print("ACTIONVANI MULTILINGUAL SPEECH TEST")
    print("=" * 55)

    print("Device:", DEVICE)

    processor, model = load_whisper()

    results = []

    for item in DATASETS:

        language = item["language"]
        input_path = item["input"]

        output_path = (
            OUTPUT_DIR
            / language
            / f"{language}_test.wav"
        )

        print("\n" + "-" * 55)
        print("Language:", language.upper())

        try:

            convert_to_wav(input_path, output_path)

            text, processing_time = transcribe_audio(
                processor,
                model,
                output_path,
                item["whisper_language"],
            )

            result = {
                "language": language,
                "source_file": input_path.name,
                "transcription": text,
                "processing_time_seconds": processing_time,
                "status": "success",
            }

            print("\nTRANSCRIPTION:")
            print(text)

            print("\nProcessing time:", processing_time, "seconds")

        except Exception as error:

            result = {
                "language": language,
                "source_file": input_path.name,
                "status": "failed",
                "error": str(error),
            }

            print("ERROR:", error)

        results.append(result)

    # ---------------------------------
    # 6. Save results
    # ---------------------------------

    results_dir = ROOT / "datasets" / "evaluation" / "speech" / "whisper_small"

    results_dir.mkdir(parents=True, exist_ok=True)

    results_path = results_dir / "transcription_results.json"

    results_path.parent.mkdir(parents=True, exist_ok=True)

    with open(results_path, "w", encoding="utf-8") as file:

        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=4,
        )

    print("\n" + "=" * 55)
    print("TESTING FINISHED")
    print("Results saved to:", results_path)
    print("=" * 55)

    if DEVICE == "cuda":
        print(
            "Peak GPU memory:",
            round(
                torch.cuda.max_memory_allocated(0) / 1024**3,
                2,
            ),
            "GB",
        )


if __name__ == "__main__":
    main()
