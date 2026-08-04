# STT Voice Transcription Pipeline — Debugging Reference

## Architecture

```
Telegram voice message
  → gateway/platforms/telegram.py (~line 3186-3260)
    msg.voice detected → get_file() → download_as_bytearray()
    → cache_audio_from_bytes(bytes, ext=".ogg") → /hermes/cache/audio/audio_<hash>.ogg
    → event.media_urls = [cached_path], event.media_types = ["audio/ogg"]

  → gateway/run.py (~line 5900-5945)
    audio_paths populated from event.media_urls where mtype.startswith("audio/")
      or message_type in (VOICE, AUDIO)
    → _enrich_message_with_transcription(user_text, audio_paths)

  → gateway/run.py (~line 11900-11970)
    _enrich_message_with_transcription():
      1. Check self.config.stt_enabled (from GatewayConfig, reads stt.enabled in yaml)
      2. from tools.transcription_tools import transcribe_audio
      3. result = await asyncio.to_thread(transcribe_audio, path)
      4. On success: prepend '[The user sent a voice message. Here's what they said: "transcript"]'
      5. On failure with "No STT provider": send user a DM with setup instructions
      6. On other failure: '[The user sent a voice message but I had trouble transcribing it]'

  → tools/transcription_tools.py
    transcribe_audio(file_path):
      1. _load_stt_config() from config.yaml
      2. is_stt_enabled() check
      3. _get_provider() resolves: local (faster-whisper) > groq > openai > mistral > xai
      4. _HAS_FASTER_WHISPER set at import time via _safe_find_spec()
      5. Calls faster_whisper.WhisperModel.transcribe()
      6. Returns {"success": bool, "transcript": str, "provider": str}
```

## Key Constants

| What | Value |
|------|-------|
| Audio cache dir | `/hermes/cache/audio/` |
| HF model cache | `/hermes/home/.cache/huggingface/hub/models--Systran--faster-whisper-<size>/` |
| STT config path | `stt:` section in `/hermes/config.yaml` |
| Gateway config class | `gateway/config.py:GatewayConfig` field `stt_enabled` |
| Module-level flag | `tools/transcription_tools._HAS_FASTER_WHISPER` (set once at import) |
| Provider resolution | `tools/transcription_tools._get_provider()` |
| Transcription function | `tools/transcription_tools.transcribe_audio()` |

## Common Failure Modes

### 1. "No STT provider" after fresh install
**Cause:** `faster-whisper` installed but model not yet downloaded from HuggingFace Hub. First transcription triggers download (~30s for `base`), but the gateway may time out or the model download may fail silently.

**Fix:** Pre-warm the model cache:
```bash
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"
```

### 2. "No STT provider" after container restart
**Cause:** `_HAS_FASTER_WHISPER` is `False` because `faster-whisper` was installed in user site-packages (`/hermes/home/.local/lib/`) which may not have been on `sys.path` at gateway startup if the volume mount wasn't ready.

**Fix:** Verify with `python3 -c "import faster_whisper; print(faster_whisper.__file__)"` — should show a path. If it fails, reinstall or check volume mount.

### 3. Voice cached but not transcribed (no log line)
**Cause:** Gateway process has stale `_HAS_FASTER_WHISPER = False` from before the package was installed. The import check only runs once.

**Fix:** Restart the gateway (`/restart` or `docker restart`).

### 4. Transcription works manually but gateway still fails
**Cause:** The gateway's `GatewayConfig.stt_enabled` may be `False` if the config wasn't read properly, or the `_enrich_message_with_transcription` function returned early due to the `stt_enabled` check.

**Debug:** Check gateway log for "Cached user voice" (confirms download happened) but no "Transcribing user voice" line (confirms transcription was skipped).

## Manual Testing Commands

```bash
# Check package importability
python3 -c "from faster_whisper import WhisperModel; print('OK')"

# Check full pipeline
python3 -c "
from tools.transcription_tools import transcribe_audio, _get_provider, _load_stt_config, is_stt_enabled, _HAS_FASTER_WHISPER
stt_config = _load_stt_config()
print('enabled:', is_stt_enabled(stt_config))
print('provider:', _get_provider(stt_config))
print('faster_whisper_available:', _HAS_FASTER_WHISPER)
"

# Transcribe a cached voice file
python3 -c "
from tools.transcription_tools import transcribe_audio
result = transcribe_audio('/hermes/cache/audio/audio_XXX.ogg')
print(result)
"

# Pre-warm model cache
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Check gateway logs for voice/STT activity
grep -i "Cached user voice\|transcri\|No STT\|stt" /hermes/logs/gateway.log | tail -20
```

## Session Reference

- 2026-05-23: Debugged STT in Docker container on VPS. Root cause: whisper model not downloaded yet when first voice message arrived. `faster-whisper` was installed in `/hermes/home/.local/lib/python3.12/site-packages` (persistent Docker volume at `/hermes`). Gateway PID 1 runs `hermes gateway run --replace`. Docker CLI not available inside container.
