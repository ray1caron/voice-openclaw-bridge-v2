# Audio I/O Configuration Guide

**Voice-OpenClaw Bridge v2**
**Version:** 0.2.0
**Last Updated:** 2026-02-27 12:22 PST
**Phase:** 5 Day 5 - Audio Input/Output Setup

This guide covers audio device configuration for the Voice-OpenClaw Bridge.

---

## Audio Devices Overview

The voice assistant requires two audio devices:

1. **Input Device (Microphone):** Captures spoken commands
2. **Output Device (Speakers):** Plays synthesized responses

---

## Device Discovery

### List Available Devices

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Use the built-in audio discovery tool
python -m bridge.audio_discovery list
```

This will show:
- Device indices
- Device names
- Supported sample rates
- Input vs output devices

### Select Default Devices

The system automatically selects default devices. Typically:
- **Input:** Default system microphone
- **Output:** Default system speakers

---

## Configuration

### Using Config File

Edit `~/.voice-bridge/config.yaml`:

```yaml
audio:
  # Input device
  input:
    device_index: -1  # -1 = system default
    sample_rate: 16000  # Recommended for Whisper
    channels: 1  # Mono is sufficient

  # Output device
  output:
    device_index: -1  # -1 = system default
    sample_rate: 22050  # Recommended for TTS
    channels: 1  # Mono is sufficient

  # Volume control
  input_gain: 1.0  # Increase microphone sensitivity
  output_volume: 1.0  # Normalize output volume
```

### Using Device Names

Instead of device indices, you can specify device names:

```yaml
audio:
  input:
    device_name: "USB Microphone"
  output:
    device_name: "Built-in Speakers"
```

The system will match by partial name.

---

## Testing Audio Devices

### Test Microphone

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

python -m audio.test_microphone
```

This will:
- Record 5 seconds of audio
- Calculate audio levels
- Display statistics

### Test Speakers

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

python -m audio.test_speakers
```

This will:
- Play a test tone
- Verify output works
- Display output statistics

---

## Common Issues & Solutions

### Issue 1: Microphone Not Detected

**Symptoms:**
- Wake word never triggers
- Audio capture returns silence
- Low audio levels

**Solutions:**
1. Check device permissions:
   ```bash
   # Linux: Add user to audio group
   sudo usermod -a -G audio $USER
   # Log out and log back in
   ```

2. Select specific device:
   ```yaml
   audio:
     input:
       device_index: 2  # Use discovered index
   ```

3. Increase input gain:
   ```yaml
   audio:
     input_gain: 2.0
   ```

4. Verify device works with system:
   ```bash
   # Linux
   arecord -f cd -d 5 test-mic.wav
   aplay test-mic.wav
   ```

### Issue 2: Speakers Not Working

**Symptoms:**
- TTS synthesis completes but no audio
- Audio playback throws errors

**Solutions:**
1. Check device permissions:
   ```bash
   # Linux: Add user to audio group
   sudo usermod -a -G audio $USER
   ```

2. Select specific device:
   ```yaml
   audio:
     output:
       device_index: 3  # Use discovered index
   ```

3. Test with system:
   ```bash
   aplay /usr/share/sounds/alsa/Front_Center.wav
   ```

### Issue 3: Low Volume

**Symptoms:**
- Microphone barely picks up voice
- TTS audio too quiet

**Solutions:**
1. Increase input/output gains:
   ```yaml
   audio:
     input_gain: 2.0
     output_volume: 2.0
   ```

2. Check system mixer settings:
   ```bash
   # Linux
   alsamixer
   # Adjust microphone and master volume
   ```

### Issue 4: Audio Latency Too High

**Symptoms:**
- Long delays before wake word triggers
- Slow response times

**Solutions:**
1. Use lower latency buffer sizes:
   ```yaml
   audio:
     buffer_size: 256  # Lower = less latency, more CPU
   ```

2. Use system-provided low-latency audio:
   - Linux: Use PipeWire instead of PulseAudio
   - macOS: Use CoreAudio (already low latency)

3. Adjust VAD silence threshold:
   ```yaml
   audio:
     silence_threshold_ms: 1000  # Lower = faster
   ```

### Issue 5: Audio Distortion/Popping

**Symptoms:**
- Cracking sounds in playback
- Choppy audio

**Solutions:**
1. Increase buffer size:
   ```yaml
   audio:
     buffer_size: 1024  # Larger = more stable
   ```

2. Update audio drivers
3. Try different audio backend (if available):
   - Linux: PortAudio (sounddevice default)
   - Try PulseAudio or PipeWire directly

---

## Device-Specific Configurations

### USB Microphones

USB microphones often work out of the box. Use default settings:

```yaml
audio:
  input:
    device_index: -1  # System default
    sample_rate: 16000
    input_gain: 1.0
```

### Bluetooth Microphones

May have latency. Increase buffer size:

```yaml
audio:
  input:
    buffer_size: 2048  # Larger buffer for Bluetooth
    input_gain: 1.5  # May need more gain
```

### Built-in Laptop Microphones

Often have noise. Increase gain:

```yaml
audio:
  input:
    input_gain: 2.0  # Boost weak signal
```

### USB Speakers

Usually work well:

```yaml
audio:
  output:
    device_index: -1
    volume: 1.0
```

### Bluetooth Speakers

May have latency. Not ideal for voice assistant (delayed feedback):

```yaml
# Not recommended for voice assistant
# Use wired/wifi speakers for better timing
audio:
  output:
    device_index: -1
```

---

## Troubleshooting Commands

### Linux

```bash
# List audio devices
python -m bridge.audio_discovery list

# Check audio groups
groups

# Test microphone
arecord -f cd -d 5 test.wav
aplay test.wav

# Adjust mixer
alsamixer

# Check audio logs
journalctl -u pulseaudio -b
```

### macOS

```bash
# List audio devices
python -m bridge.audio_discovery list

# Test microphone
sox -d test.wav
play test.wav
```

---

## Best Practices

1. **Use USB Microphone:** Better quality control and usually lower noise
2. **Use Wired Speakers:** Bluetooth has latency, affects timing
3. **Mic Positioning:** Place 6-12 inches away, not too close (popping) or too far (weak)
4. **Quiet Environment:** Background noise affects wake word detection
5. **Test First:** Always test devices with system commands before running voice assistant

---

## Advanced Configuration

### Low Priority Audio

To prevent audio issues during other tasks:

```yaml
audio:
  priority: "low"  # Don't block other audio
```

### High Priority Audio

For dedicated voice assistant hardware:

```yaml
audio:
  priority: "high"  # Prioritize audio
```

### Exclusive Mode

Lock audio device to this application:

```yaml
audio:
  exclusive: true  # Only voice assistant uses device
```

**Warning:** This prevents other apps from using audio simultaneously.

---

**Last Updated:** 2026-02-27
**Phase 5 Day 5 Complete**
**Next:** Day 6 End-to-End Testing