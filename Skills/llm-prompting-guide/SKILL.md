---
name: llm-prompting-guide
description: Prompt format rules for generative video and music models. Use when writing or reviewing a prompt for MiniMax H3 (text/image/reference-to-video with native audio) or MiniMax Music 3 (song generation from caption plus lyrics), in ComfyUI or elsewhere. Do NOT use for chat-assistant prompts, or for generative models not named here.
---

# LLM Prompting Guide

The models below were trained on prompts written in a specific labelled structure, and guessing at that structure degrades output. Read the full guide for the model in play before writing any prompt text; the bullet here is a router, not enough to draft from.

- MiniMax H3 (video + native stereo audio; T2VA, I2VA, FL2VA, L2VA, R2V) -> [references/minimax-h3.md](references/minimax-h3.md)
- MiniMax Music 3 (full songs from a structured caption + tagged lyrics) -> [references/minimax-music-3.md](references/minimax-music-3.md)

Adding a model: one bullet above, plus `references/<model>.md` opening with a table of contents and a mode-selection table.
