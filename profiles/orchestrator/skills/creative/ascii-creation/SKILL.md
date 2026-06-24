---
name: ascii-creation
description: "ASCII art and animation: text banners, cowsay, image-to-ascii, video-to-ASCII, audio-reactive ASCII animation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ASCII, Art, Animation, Banners, Creative, Unicode, Text-Art, Video, pyfiglet, figlet, cowsay, boxes]
    category: creative
---

# ASCII Creation Suite

Two modes: **static ASCII art** (banners, decorative borders, image conversion) and **ASCII video/animation** (converting video/audio to animated ASCII MP4/GIF with creative direction).

---

## Mode A: Static ASCII Art

9 tools for different ASCII art needs. All local CLI or free REST APIs — no API keys.

### Text Banners (pyfiglet — local, 571 fonts)
```bash
pip install pyfiglet --break-system-packages -q
python3 -m pyfiglet "YOUR TEXT" -f slant    # Recommended: slant, doom, big, banner3
python3 -m pyfiglet --list_fonts
```
**Fallback API** (no install): `curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello"`

### Cowsay (Message Art)
```bash
sudo apt install cowsay -y
cowsay "Hello" | cowsay -f tux | cowsay -f dragon  # 50+ characters
cowthink "Hmm..."                                    # Thought bubble
```

### Boxes (Decorative Borders, 70+ designs)
```bash
sudo apt install boxes -y
echo "Hello" | boxes -d stone | boxes -d cat | boxes -d unicornsay
# Combine: python3 -m pyfiglet "HERMES" -f slant | boxes -d stone
```

### Image to ASCII
- **ascii-image-converter** (recommended): `ascii-image-converter image.png -C` (color)
- **jp2a** (lightweight, JPEG only): `jp2a --width=80 --colors image.jpg`

### Pre-Made ASCII Art Search
Fetch from ascii.co.uk via curl + Python extraction. Available subjects: animals, objects, nature, characters, holidays.

### Fun Utilities
- **QR codes**: `curl -s "qrenco.de/https://example.com"`
- **Weather**: `curl -s "wttr.in/London"`
- **Octocat**: `curl -s https://api.github.com/octocat`

### Decision Flow
1. Text as banner → pyfiglet (installed) or asciified API (no install)
2. Wrap message in fun character → cowsay
3. Decorative border → boxes (can combine with pyfiglet)
4. Art of specific thing → ascii.co.uk via curl
5. Convert image → ascii-image-converter or jp2a
6. Custom/creative → LLM generation with Unicode palette (box drawing, block elements, geometric symbols)

---

## Mode B: ASCII Video Production Pipeline

Converts video/audio/images into colored ASCII character video output (MP4, GIF). Covers: video-to-ASCII, audio-reactive visualizers, generative ASCII animations, hybrid video+audio reactive, text/lyrics overlays.

### Creative Standard
This is visual art. ASCII characters are the medium; cinema is the standard. Articulate creative concept BEFORE writing code. First-render excellence is non-negotiable.

### Modes
| Mode | Input | Output |
|------|-------|--------|
| Video-to-ASCII | Video file | ASCII recreation |
| Audio-reactive | Audio file | Generative visuals driven by audio |
| Generative | Seed params | Procedural ASCII animation |
| Hybrid | Video + audio | ASCII video with audio-reactive overlays |
| Lyrics/text | Audio + text/SRT | Timed text with visual effects |

### Pipeline Architecture
```
INPUT → ANALYZE → SCENE_FN → TONEMAP → SHADE → ENCODE
```
1. **INPUT** — Load/decode source
2. **ANALYZE** — Extract per-frame features (audio FFT, video luminance, motion vectors)
3. **SCENE_FN** — Render to pixel canvas, compose character grids
4. **TONEMAP** — Percentile-based adaptive brightness normalization
5. **SHADE** — Post-processing via ShaderChain + FeedbackBuffer
6. **ENCODE** — Pipe raw RGB frames to ffmpeg for H.264/GIF

### Critical Notes
- **Brightness**: Use `tonemap()`, NOT linear `canvas * N` multipliers (they clip highlights)
- **Font cell height**: macOS Pillow `textbbox()` returns wrong height; use `font.getmetrics()`
- **ffmpeg pipe deadlock**: Never `stderr=subprocess.PIPE` with long-running ffmpeg
- **Per-clip architecture**: For segmented videos, render each as separate clip file for parallel rendering
- **Performance target**: ~100-200ms/frame (character render is bottleneck at 80-150ms)

### Aesthetic Dimensions
Character palettes (density ramps, scripts, braille), color strategies (HSV, OKLAB, discrete RGB), background textures (fBM noise, domain warp, voronoi), primary effects (rings, spirals, waves, aurora), particles (sparks, snow, boids, trails), shader moods (CRT, glitch, cinematic), coordinate spaces (cartesian, polar, fisheye), feedback (zoom tunnel, rainbow trails), masking, transitions.

### Per-Section Variation Rules
Never use same config for entire video. For each section: different background effect, different character palette, different color strategy, vary shader intensity, different particle types.

### Creative Divergence Strategies
- **Forced Connections**: Pick unrelated domain, map visual/structural elements onto ASCII
- **Conceptual Blending**: Map correspondences between two visual/conceptual spaces
- **Oblique Strategies**: "Honor thy error as a hidden intention" / "Turn it upside down" / "Only a part"