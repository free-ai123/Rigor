---
name: music-creation
description: "Music creation and analysis: songwriting craft, Suno AI prompts, HeartMuLa song generation from lyrics + tags, and audio spectrogram features via CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [music, songwriting, Suno, audio-analysis, spectrogram, AI-music]
---

# Music Creation

## Section A: Songwriting & AI Music (songwriting-and-ai-music)

### Songwriting Craft
- Structure: verse → chorus → verse → chorus → bridge → chorus
- Lyrics: match rhythm to melody, use concrete imagery, avoid clichés
- Hooks: memorable, repeatable, emotionally resonant

### Suno AI Music Prompts
- Format: `[style], [mood], [tempo], [instruments], [vocal-type]`
- Examples: `indie folk, warm acoustic guitar, soft male vocals, 90bpm`
- Use tags for genre blending: `pop-punk meets jazz fusion`
- Specify structure in lyrics with section markers: `[Verse]`, `[Chorus]`, `[Bridge]`

## Section B: HeartMuLa (heartmula)

Generate songs from lyrics + tags. Alternative to Suno with more control over the generation pipeline.

- Input: lyrics text + style tags
- Output: generated audio
- Use when Suno is unavailable or when you need programmatic control

## Section C: Audio Analysis (songsee)

Analyze audio files via CLI for spectrograms, chroma, MFCC, and other features.

- **Mel spectrogram** — frequency content over time
- **Chroma** — pitch class representation (C, C#, D, etc.)
- **MFCC** — timbral features for classification
- Use for: understanding audio content, debugging music generation, feature extraction
