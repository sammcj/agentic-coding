# Models, setup, and the audio-to-score bridge

Targets YuE2 inference runtime **0.1.6** and the SheetSage2 and MERT-v2 Transformers interfaces. Record model and code revisions in each run manifest.

Contents:

- What connects to what
- Environments
- Transcription API
- Outputs
- Notation and rendering
- Optional MERT representations
- Distribution and licence boundaries

## What connects to what

- `m-a-p/YuE2-3B` - style and lyrics -> optional symbolic plan -> semantic tokens -> acoustic latents. Generation and regeneration after editing.
- `m-a-p/YuE2-Vae` - default listening decoder, acoustic latents -> stereo audio.
- `m-a-p/YuE2-Vae-legacy` - benchmark decoder. Decodes the same latents when reproducing the recorded evaluation protocol.
- `m-a-p/SheetSage2` - audio -> melody, chords, beats, key, structure, ABC, MIDI. Cover/edit starting score, or inspection of generated audio.
- `m-a-p/MERT-v2-FullSong` - SheetSage2's auto-loaded encoder parent. Also usable alone for continuous features.
- `m-a-p/MERT-v2-30s` - optional feature extractor for short recordings. Not needed for generation, cover, or editing.

Cover chain:

```text
source audio
  -> SheetSage2 (auto-loads its MERT-v2-FullSong parent)
  -> melody_only=True -> inspect/correct melody ABC without chord symbols
  -> YuE2-3B with cot="melody", target style, target lyrics
  -> acoustic latents -> YuE2-Vae -> listening audio
```

- Score edit: keep or revise the chord symbols and use `cot="full"`.
- Agentic editing: the agent edits the exported score and prompts between planning and regeneration. There is no separate "agentic" model API.
- MERT-v2 encoders are bidirectional and return continuous features; YuE2's semantic tokens come from a distinct causal tokeniser lineage. Plain generation needs no MERT call, so feed YuE2 ABC and prompts, never MERT embeddings.

## Environments

The releases pin different PyTorch, Transformers, and NumPy versions, so use one environment per model and exchange audio/ABC/MIDI files between them. A shared Hugging Face cache is fine. Run stages sequentially so GPU memory is released before the next model loads.

### YuE2

Release card: Linux, Python 3.10+, 24 GB NVIDIA GPU with BF16. The package installs its own pins (PyTorch 2.10.0, Transformers 4.57.6, NumPy 2.2.6). Install from the official git URL or a local clone; similarly named PyPI packages are unverified.

```bash
python3.12 -m venv .venv-yue2
.venv-yue2/bin/python -m pip install \
  git+https://github.com/multimodal-art-projection/YuE.git
# or: .venv-yue2/bin/python -m pip install /path/to/YuE
```

Current repository code and this skill are Apache 2.0.

### Apple Silicon (MPS)

Stock YuE2 runs on MPS unpatched: `device="auto"` picks `cuda`, then `mps`, then `cpu`. Same install steps; the pinned torch 2.10 wheel includes Metal support.

- Run generation outside any macOS sandbox; inside one `torch.backends.mps.is_available()` is False.
- Set `HF_HUB_ENABLE_HF_TRANSFER=0`; the first download fails if that variable is on and `hf_transfer` is absent.
- Set `--memory-budget-gib` to about a third of unified memory. It is only enforced on CUDA but sizes the VAE decode tiles.
- Stock throughput on an M5 Max: about 3.2 s of compute per second of audio (25 tok/s semantic, 72 ms per NAR frame). CUDA graphs, vLLM and FP8 are unavailable.
- `assets/mps-performance.patch` brings that to about 0.9 s per audio second when ABC is supplied. bmm attention replaces the slow MPS SDPA kernel in AR decode and NAR; `quantization="auto"` (new default) enables int8 AR linears on MPS, keeping embeddings, `lm_head` and NAR layers bf16. Both are gated on `device.type == "mps"`, so CUDA behaviour is unchanged. `YUE2_MPS_SDPA=1` reverts the attention change, `--quantization none` the int8. Written against upstream commit `88da114`.

```bash
git clone https://github.com/multimodal-art-projection/YuE.git
git -C YuE checkout 88da114a67df892af0329472073b96a5ef700b93
git -C YuE apply <skill>/assets/negative-style.patch     # any device; adds the negative_style request field
git -C YuE apply <skill>/assets/mps-performance.patch    # Apple Silicon only; apply second
.venv-yue2/bin/python -m pip install -e ./YuE
```

`negative-style.patch` does not touch device code: apply it alone on CUDA for `negative_style` (generation-and-covers.md, "Steer away from generic renditions").

- [smcleod/YuE2-3B-int8-ar](https://huggingface.co/smcleod/YuE2-3B-int8-ar) is the same int8 AR scheme saved as a 5.85 GB checkpoint (`--model smcleod/YuE2-3B-int8-ar`). Needs the patch; same speed as runtime `auto`, saves 1.4 GB of download. MPS only; slower than bf16 on CUDA.

### SheetSage2

No `pip install sheetsage2` distribution exists. Download the snapshot, install its requirements, load through Transformers. Python 3.10 or 3.11. FFmpeg 6.1 plus shared libraries from the host's package/container tools, with `ffmpeg` on `PATH`.

```bash
python3.11 -m venv .venv-sheetsage2
.venv-sheetsage2/bin/python -m pip install huggingface-hub==0.36.0
.venv-sheetsage2/bin/huggingface-cli download m-a-p/SheetSage2 \
  --local-dir models/SheetSage2
.venv-sheetsage2/bin/python -m pip install \
  torch==2.8.0 torchaudio==2.8.0 \
  --index-url https://download.pytorch.org/whl/cu126
.venv-sheetsage2/bin/python -m pip install \
  -r models/SheetSage2/requirements.txt
```

- Requirements pin Transformers 4.45.2 and NumPy 1.24.3.
- Loading the adapter snapshot fetches the exact MERT-v2-FullSong parent named in its config, checks its files, and merges adapters in FP32. Keep that parent as configured rather than substituting MERT-v2-30s or another FullSong revision.
- `trust_remote_code=True` executes the repository's Python. Pin a reviewed revision and record it with the outputs.

## Transcription API

`scripts/transcribe.py` is the normal path (see `--help`). Direct Python use:

```python
model = AutoModel.from_pretrained(
    "models/SheetSage2", trust_remote_code=True,
).eval().to(device)
result = model.transcribe(
    "source.wav", output_dir="runs/source-score",
    dtype="bf16",             # or "fp32" on CPU
    prompts=("timestamp", "downbeat_meter", "structure", "key",
             "chord_full", "melody_full"),
    melody_only=False,
)
```

Variants:

- Hub loading: use the repository ID and pass the recorded commit to both `revision` and `code_revision`.
- Vocal melody only, no chord conditioning: `prompts=("timestamp", "downbeat_meter", "structure", "key", "melody_vocal")` with `melody_only=True`. `melody_full` keeps both vocal and instrumental tracks; the default six prompts suit harmony-aware editing.
- Model CLI: `models/SheetSage2/infer.py song.mp3 --output cover-score --melody-only`.
- `preset="paper"` fixes overlap to 100 s and lookahead to zero, uses the recorded audio frontend, and changes generation stopping. Use only when reproducing that evaluation protocol with its recorded task prompts.

`melody_only=True`:

- Keeps both `Vocal` and `Ins` melodies; omits chord symbols from ABC and chord accompaniment from playback/combined MIDI.
- Changes exports, not inference. Raw chord events and LAB annotations remain when the selected tasks include chord prediction.
- `transcribe.py --task melody-full` and `--task melody-vocal` set it but drop the chord tasks. Use a direct default-task call when raw chord annotations matter.
- If melody-only ABC cannot be built, Python raises `RuntimeError` with the completed transcription on `error.result`; the CLI exits nonzero. Saved annotations alone are a failed cover score.

After every transcription, before regeneration:

1. Inspect `warnings`, `diagnostics`, and `abc_error`.
2. Read the score. Valid notation can still hold musical errors.

Input and window facts:

- Tasks are fixed names. `chord_full`/`chord_majmin` are mutually exclusive, as are `melody_full`/`melody_vocal`. Timed export requires `timestamp`; usable ABC also needs decoded beats and key.
- Paths, encoded bytes, and binary streams are decoded, mixed to mono, resampled to 24 kHz.
- Arrays and tensors need `sampling_rate` and shape `[samples]` or `[channels, samples]`. `soundfile.read(..., always_2d=True)` returns `[samples, channels]`, so transpose first.
- Minimum 1,025 finite samples after resampling. A short clip may still lack beats or key for ABC.
- Defaults: 300 s windows, 200 s overlap, 100 s lookahead. `max_seconds` crops the input rather than limiting memory. Reduced overlap requires `0 <= lookahead <= overlap < 300`.
- Logits and all-layer exports are large; leave them off for cover/edit work. Size workloads from reported `peak_gpu_mib` and window statistics.

## Outputs

- `result["abc"]` - string, or `None` on notation failure in full mode -> `score.abc`
- `result["midi"]` - combined playback bytes, chords omitted under `melody_only` -> `transcription.mid`
- `result["midis"]["melody" | "melody_vocal" | "melody_instrumental"]` - bytes -> `melody.mid`, `melody_vocal.mid`, `melody_instrumental.mid`
- `result["midis"]["chords"]` - bytes, no notes under `melody_only` -> `chords.mid`
- `result["events"]` list and `result["num_events"]` count -> `events.json`
- `result["labs"]` - mapping -> `beat.lab`, `downbeat.lab`, `key.lab`, `chord.lab`, `structure.lab`, melody LABs
- `result["tokens"]` - per-window token IDs -> `tokens.json`, `tokens.txt`
- `result["tensors"]` - CPU tensors by window -> `tensors/` when requested with an output directory

Notes:

- `output_dir=None` keeps results in memory.
- Saved `result.json` stores `events` as an integer count. The Python `result["events"]` is a list. Read each by its own schema.
- `notation/` holds the beat grid, intervals, and monophonic MIDI used for score reconstruction. Raw MIDI keeps timing that quantised notation simplifies.

## Notation and rendering

The exported ABC comes from SheetSage2's two-voice serialiser, validated against the reconstructed score. The bundled `notation_sheetsage2` module exposes:

```text
generate_abc_from_exports(melody_midi_path, *, output_path=None,
                          meter_conflict="infer", melody_only=False)
# -> (abc_text, score_object, companion_paths)
generate_abc_from_data(melody_midi, beats, chords, keys, structures, *,
                      meter_conflict="infer", melody_only=False)
# -> (abc_text, score_object)
score_to_abc(score_object)              # validates its own serialisation
validate_serialized_abc(text, score_object)
```

- Not a general ABC parser; no `validate_abc(text)` exists. Check agent-authored ABC with the skill's own checks (duration, voice, pitch, edit preservation).
- To strip chords from an existing full transcription without re-running inference, import the module from `model.__class__.__module__`'s package and call `generate_abc_from_exports("runs/source-score/notation/song_melody.mid", melody_only=True)`.
- The file helper needs the exact `*_melody.mid` name plus sibling `*_beats.txt`, `*_keys.txt`, `*_structures.txt` (full score also `*_chords.txt`). Beat grid and key come from those files, never from an arbitrary MIDI.

Rendering is optional and uses no YuE2 VAE:

```bash
.venv-sheetsage2/bin/python models/SheetSage2/setup_render.py   # --with-deps on minimal Linux
.venv-sheetsage2/bin/python models/SheetSage2/infer.py source.wav \
  --output runs/source-score --render-audio --render-score pdf,svg,png
.venv-sheetsage2/bin/python models/SheetSage2/render.py \
  --input runs/source-score --output runs/source-rendered \
  --audio --score pdf,svg,png
```

- Piano preview plays MIDI timing; sheet rendering reads ABC.
- Editing `score.abc` does not update the existing MIDI, so the preview can still play old notes. Regenerate MIDI from the edited ABC with a compatible converter before judging piano audio.

Offline use: `model.save_pretrained("models/SheetSage2-merged")`, then load with `local_files_only=True`. The merged save removes the adapter-only snapshot's dependency on its parent files.

## Optional MERT representations

For a separate retrieval or analysis tool only. Not needed between SheetSage2 and YuE2. Embedding distance alone does not establish melodic or harmonic fidelity.

```bash
python3.11 -m venv .venv-mert2
.venv-mert2/bin/python -m pip install \
  torch==2.6.0 torchaudio==2.6.0 transformers==4.53.2 \
  huggingface-hub safetensors soundfile
```

```python
repo = "m-a-p/MERT-v2-FullSong"  # or m-a-p/MERT-v2-30s
processor = AutoFeatureExtractor.from_pretrained(repo, trust_remote_code=True)
encoder = AutoModel.from_pretrained(repo, trust_remote_code=True).eval().to(device)
inputs = processor(mono_24k, sampling_rate=processor.sampling_rate,
                   return_tensors="pt").to(device)
with torch.inference_mode():
    output = encoder(**inputs, output_hidden_states=True)
mask = output.feature_attention_mask[..., None]
embedding = (output.last_hidden_state * mask).sum(1) / mask.sum(1).clamp_min(1)
```

- Input 24 kHz mono; output 25 Hz, 1,024-dimensional frames.
- `hidden_states` has 24 post-block tensors. Index 0 is block 1 output, not the input embedding.
- FullSong is adapted to 30-360 s. Chunk longer recordings yourself; the low-level model lacks SheetSage2's whole-song stitching.

## Distribution and licence boundaries

- Model weights are **CC BY-NC 4.0** per the checked model cards. This skill's licence does not relicense them or lift the noncommercial terms.
- Link users to each model's `LICENSE` and `THIRD_PARTY_NOTICES.md`. Call installed renderers rather than redistributing them.

Model cards:

- [YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B)
- [YuE2-Vae](https://huggingface.co/m-a-p/YuE2-Vae)
- [YuE2-Vae-legacy](https://huggingface.co/m-a-p/YuE2-Vae-legacy)
- [SheetSage2](https://huggingface.co/m-a-p/SheetSage2)
- [MERT-v2-FullSong](https://huggingface.co/m-a-p/MERT-v2-FullSong)
- [MERT-v2-30s](https://huggingface.co/m-a-p/MERT-v2-30s)
