"""
Generate test audio files for voice assistant testing.

Creates sample audio files with:
- Silence (for testing silence detection)
- Spoken text (for STT testing)
- Different volumes (for testing normalization)

Usage:
    python3 generate_test_audio.py
"""

import numpy as np
import soundfile as sf
import os
from pathlib import Path


def generate_silence(duration_s=2.0, sample_rate=16000):
    """Generate silence audio."""
    samples = int(duration_s * sample_rate)
    audio = np.zeros(samples, dtype=np.float32)
    return audio, sample_rate


def generate_tone(frequency_hz=440, duration_s=2.0, sample_rate=16000, amplitude=0.5):
    """Generate a pure sine wave tone."""
    samples = int(duration_s * sample_rate)
    t = np.linspace(0, duration_s, samples, False)
    audio = amplitude * np.sin(2 * np.pi * frequency_hz * t)
    return audio.astype(np.float32), sample_rate


def generate_speech_like(duration_s=2.0, sample_rate=16000, amplitude=0.3):
    """
    Generate speech-like audio (pseudo-random modulated noise).

    This approximates speech for testing purposes without real voice samples.
    """
    samples = int(duration_s * sample_rate)
    t = np.linspace(0, duration_s, samples, False)

    # Create modulated noise that sounds somewhat like speech
    voice = np.random.uniform(-1, 1, samples) * amplitude

    # Add amplitude modulation (speech has varying amplitude)
    modulator = np.sin(2 * np.pi * 3 * t)  # 3 Hz modulation (syllable rate)
    voice = voice * (0.5 + 0.5 * modulator)

    # Add simple formant-like emphasis using moving average
    window = 10
    weights = np.ones(window) / window
    voice = np.convolve(voice, weights, mode='same')

    return voice.astype(np.float32), sample_rate


def save_audio(audio, sr, filepath):
    """Save audio as WAV file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Save as FLAC for lossless compression
    sf.write(str(filepath), audio, sr, format='FLAC')

    # Also save as WAV for compatibility
    wav_path = str(filepath).replace('.flac', '.wav')
    sf.write(wav_path, audio, sr, format='WAV')

    print(f"✓ Created: {filepath}")


def main():
    """Generate all test audio files."""
    output_dir = Path("tests/fixtures/audio")
    sr = 16000  # Standard for Whisper/STT

    print("Generating test audio files...")

    # 1. Silence - for testing silence detection
    silence, _ = generate_silence(duration_s=2.0, sample_rate=sr)
    save_audio(silence, sr, output_dir / "silence_2s.flac")

    # 2. Tone - for testing audio path (not STT)
    tone, _ = generate_tone(frequency_hz=440, duration_s=2.0,
                           sample_rate=sr, amplitude=0.5)
    save_audio(tone, sr, output_dir / "tone_440hz_2s.flac")

    # 3. Speech-like - for testing STT pipeline
    speech, _ = generate_speech_like(duration_s=2.0, sample_rate=sr,
                                   amplitude=0.3)
    save_audio(speech, sr, output_dir / "speech_like_2s.flac")

    # 4. Short phrase - for quick tests
    short_speech, _ = generate_speech_like(duration_s=1.0, sample_rate=sr,
                                        amplitude=0.3)
    save_audio(short_speech, sr, output_dir / "speech_short_1s.flac")

    # 5. Long phrase - for testing longer transcriptions
    long_speech, _ = generate_speech_like(duration_s=5.0, sample_rate=sr,
                                       amplitude=0.3)
    save_audio(long_speech, sr, output_dir / "speech_long_5s.flac")

    # 6. Low volume - for testing normalization
    low_speech, _ = generate_speech_like(duration_s=2.0, sample_rate=sr,
                                      amplitude=0.05)
    save_audio(low_speech, sr, output_dir / "speech_low_volume.flac")

    # 7. High volume - for testing clipping
    high_speech, _ = generate_speech_like(duration_s=2.0, sample_rate=sr,
                                       amplitude=0.9)
    save_audio(high_speech, sr, output_dir / "speech_high_volume.flac")

    # 8. Multi-channel (stereo) - for testing channel handling
    stereo_speech = np.column_stack([
        generate_speech_like(duration_s=2.0, sample_rate=sr, amplitude=0.3)[0],
        generate_speech_like(duration_s=2.0, sample_rate=sr, amplitude=0.3)[0]
    ])
    save_audio(stereo_speech, sr, output_dir / "speech_stereo_2s.flac")

    print(f"\n✓ All test audio files generated in: {output_dir.resolve()}")
    print(f"  Total files: 8 (.flac + .wav each)")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Format: FLAC (lossless) + WAV (compatibility)")

    # List generated files
    print("\nGenerated files:")
    for f in sorted(output_dir.glob("*.flac")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()