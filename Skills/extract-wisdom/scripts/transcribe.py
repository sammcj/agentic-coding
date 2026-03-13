#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "onnx-asr[cpu,hub] @ git+https://github.com/istupakov/onnx-asr.git",
# ]
# ///
"""Transcribe audio to text using NVIDIA Parakeet TDT v2 (ONNX INT8).

Standalone script called by wisdom.py as a fallback when YouTube subtitles
are not available. Uses Silero VAD for segmenting long audio files and
WeSpeaker embeddings for automatic speaker detection.

The model and dependencies are only downloaded on first use (~2.5 GB model).
Runs on CPU at ~36x real-time on modern hardware (a 1-hour video takes ~100s).

Usage:
    uv run transcribe.py <audio_file> <output_file>
"""

from __future__ import annotations

import argparse
import os
import sys
import wave
from pathlib import Path


def _suppress_ort_logging() -> None:
    """Suppress noisy ONNX Runtime and CoreML warnings."""
    os.environ["ORT_LOG_LEVEL"] = "3"
    os.environ["COREML_DELEGATE_NO_SYNC"] = "1"


def _create_session_options():
    """Create ONNX Runtime session options using all available CPU cores."""
    import onnxruntime as rt

    sess = rt.SessionOptions()
    sess.log_severity_level = 3
    cpu_count = os.cpu_count() or 4
    sess.intra_op_num_threads = cpu_count
    sess.inter_op_num_threads = min(4, cpu_count)
    return sess


# Force CPU-only to avoid CoreML memory bloat on macOS.
_PROVIDERS = ["CPUExecutionProvider"]


def _load_wav_audio(audio_path: Path):
    """Load WAV file as a float32 numpy array and sample rate."""
    import numpy as np

    with wave.open(str(audio_path), "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())

    if sampwidth == 2:
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    elif sampwidth == 1:
        audio = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth}")

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    return audio, sample_rate


def _detect_speakers(segments, audio, sample_rate, sess_options) -> list[int]:
    """Assign speaker IDs to each segment using WeSpeaker embeddings.

    Uses greedy cosine-similarity clustering: each new segment is compared
    against existing speaker centroids. If the best match exceeds the
    threshold it is assigned to that speaker, otherwise a new speaker is
    created. Segments shorter than 1 second are assigned to the nearest
    neighbour since short clips produce unreliable embeddings.
    """
    import numpy as np
    from onnx_asr.loader import Manager  # type: ignore[arg-type]

    manager = Manager(sess_options=sess_options, providers=_PROVIDERS)
    se = manager.create_se("wespeaker/wespeaker-voxceleb-resnet34")

    min_duration = 1.0
    threshold = 0.65
    embeddings: list = [None] * len(segments)
    valid_indices: list[int] = []

    for i, seg in enumerate(segments):
        duration = seg.end - seg.start
        if duration < min_duration:
            continue
        start_sample = int(seg.start * sample_rate)
        end_sample = int(seg.end * sample_rate)
        segment_audio = audio[start_sample:end_sample]
        if len(segment_audio) < int(sample_rate * min_duration):
            continue
        embeddings[i] = se.embedding(segment_audio, sample_rate=sample_rate)
        valid_indices.append(i)

    if len(valid_indices) < 2:
        return [0] * len(segments)

    # Greedy clustering against running speaker centroids.
    speaker_ids = [-1] * len(segments)
    centroids: list = []
    centroid_counts: list[int] = []

    for i in valid_indices:
        emb = embeddings[i]
        if emb is None:
            continue
        best_speaker = -1
        best_sim = -1.0
        for s_id, centroid in enumerate(centroids):
            norm = float(np.linalg.norm(emb) * np.linalg.norm(centroid))
            if norm == 0:
                continue
            sim = float(np.dot(emb, centroid) / norm)
            if sim > best_sim:
                best_sim = sim
                best_speaker = s_id

        if best_sim >= threshold and best_speaker >= 0:
            speaker_ids[i] = best_speaker
            n = centroid_counts[best_speaker]
            centroids[best_speaker] = (centroids[best_speaker] * n + emb) / (n + 1)
            centroid_counts[best_speaker] += 1
        else:
            speaker_ids[i] = len(centroids)
            centroids.append(np.copy(emb))
            centroid_counts.append(1)

    # Assign short/skipped segments to their nearest resolved neighbour.
    for i in range(len(segments)):
        if speaker_ids[i] >= 0:
            continue
        for delta in range(1, len(segments)):
            for j in (i - delta, i + delta):
                if 0 <= j < len(segments) and speaker_ids[j] >= 0:
                    speaker_ids[i] = speaker_ids[j]
                    break
            if speaker_ids[i] >= 0:
                break
        if speaker_ids[i] < 0:
            speaker_ids[i] = 0

    # Merge tiny clusters into their nearest significant speaker.
    # Speakers with < 3% of total segments (min 3) are noise from tone
    # shifts, background audio, etc.
    min_cluster = max(3, int(len(segments) * 0.03))
    from collections import Counter
    counts = Counter(speaker_ids)
    small_ids = {s for s, c in counts.items() if c < min_cluster}
    if small_ids and len(counts) - len(small_ids) >= 1:
        large_ids = [s for s in counts if s not in small_ids]
        remap: dict[int, int] = {}
        for s_id in small_ids:
            best_target = large_ids[0]
            best_sim = -1.0
            for t_id in large_ids:
                norm = float(np.linalg.norm(centroids[s_id]) * np.linalg.norm(centroids[t_id]))
                if norm == 0:
                    continue
                sim = float(np.dot(centroids[s_id], centroids[t_id]) / norm)
                if sim > best_sim:
                    best_sim = sim
                    best_target = t_id
            remap[s_id] = best_target
        speaker_ids = [remap.get(s, s) for s in speaker_ids]

        # Re-number speaker IDs to be contiguous from 0.
        unique_sorted = sorted(set(speaker_ids))
        renumber = {old: new for new, old in enumerate(unique_sorted)}
        speaker_ids = [renumber[s] for s in speaker_ids]

    return speaker_ids


def transcribe(audio_path: Path) -> str:
    """Transcribe audio using Parakeet TDT v2 INT8 with Silero VAD."""
    import onnx_asr  # type: ignore[import-untyped]

    _suppress_ort_logging()
    sess_options = _create_session_options()

    print("Loading model...", file=sys.stderr)
    model = onnx_asr.load_model(
        "nemo-parakeet-tdt-0.6b-v2",
        quantization="int8",
        sess_options=sess_options,
        providers=_PROVIDERS,
    )

    vad = onnx_asr.load_vad(
        "silero", sess_options=sess_options, providers=_PROVIDERS,
    )
    model = model.with_vad(
        vad,
        max_speech_duration_s=60.0,
        min_silence_duration_ms=2000.0,
        speech_pad_ms=100.0,
    )

    print("Transcribing...", file=sys.stderr)
    segments = list(model.recognize(str(audio_path)))
    print(f"Transcribed {len(segments)} segments", file=sys.stderr)

    if not segments:
        return ""

    # Detect multiple speakers via WeSpeaker embeddings.
    try:
        audio, sample_rate = _load_wav_audio(audio_path)
        speaker_ids = _detect_speakers(segments, audio, sample_rate, sess_options)
        num_speakers = len(set(speaker_ids))
    except Exception:
        speaker_ids = [0] * len(segments)
        num_speakers = 1

    # Extract text and matching speaker IDs, skipping empty segments.
    texts: list[str] = []
    text_speaker_ids: list[int] = []
    for seg, spk in zip(segments, speaker_ids):
        text = seg.text.strip() if hasattr(seg, "text") else str(seg).strip()
        if text:
            texts.append(text)
            text_speaker_ids.append(spk)

    # Strip overlapping prefix words between consecutive segments.
    for i in range(1, len(texts)):
        prev_words = texts[i - 1].split()
        curr_words = texts[i].split()
        max_overlap = min(8, len(prev_words), len(curr_words))
        best = 0
        for n in range(1, max_overlap + 1):
            if [w.lower() for w in prev_words[-n:]] == [w.lower() for w in curr_words[:n]]:
                best = n
        if best > 0:
            texts[i] = " ".join(curr_words[best:])

    parts: list[str] = []
    multi = num_speakers > 1
    for text, spk in zip(texts, text_speaker_ids):
        if not text:
            continue
        if multi:
            parts.append(f"Speaker {spk + 1}: {text}")
        else:
            parts.append(text)

    return "\n\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe audio using Parakeet TDT v2 (ONNX INT8)",
    )
    parser.add_argument("audio_file", help="Path to audio file (WAV format)")
    parser.add_argument("output_file", help="Output transcript file path")

    args = parser.parse_args()
    audio_path = Path(args.audio_file)
    output_path = Path(args.output_file)

    if not audio_path.is_file():
        print(f"Error: Audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    text = transcribe(audio_path)

    if not text.strip():
        print("Error: Transcription produced no text", file=sys.stderr)
        sys.exit(1)

    output_path.write_text(text, encoding="utf-8")
    print(f"TRANSCRIPT_PATH: {output_path}")


if __name__ == "__main__":
    main()
