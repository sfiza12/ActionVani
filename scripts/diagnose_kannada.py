
import torch
import soundfile as sf

from transformers import (
    AutoProcessor,
    AutoModelForSpeechSeq2Seq,
)

MODEL_ID = "openai/whisper-small"

AUDIO_PATH = (
    "datasets/processed_audio/kannada/kannada_test.wav"
)

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

print("Loading processor...")
processor = AutoProcessor.from_pretrained(MODEL_ID)

print("Loading model...")
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_ID,
    dtype=dtype,
    low_cpu_mem_usage=True,
).to(device)

model.eval()

# Check Kannada language token
language_tokens = model.generation_config.lang_to_id

print("\nCHECKING KANNADA SUPPORT")

kannada_tokens = [
    token for token in language_tokens
    if "kn" in token.lower()
]

print("Kannada tokens:", kannada_tokens)

if not kannada_tokens:
    raise RuntimeError("Kannada token not found in model configuration")

# Load audio
audio, sr = sf.read(AUDIO_PATH)

inputs = processor(
    audio,
    sampling_rate=sr,
    return_tensors="pt",
)

features = inputs.input_features.to(
    device=device,
    dtype=dtype,
)

# Test with the modern generation interface
print("\nTRANSCRIBING WITH EXPLICIT KANNADA")

with torch.inference_mode():
    generated = model.generate(
        features,
        language="kannada",
        task="transcribe",
        num_beams=5,
        max_new_tokens=128,
    )

text = processor.batch_decode(
    generated,
    skip_special_tokens=True,
    clean_up_tokenization_spaces=False,
)[0]

print("\nFINAL TRANSCRIPTION:")
print(repr(text))

print("\nDIAGNOSTIC FINISHED")
