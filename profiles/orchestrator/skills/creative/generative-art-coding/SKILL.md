---
name: generative-art-coding
description: "Code-based generative art: Manim CE (3Blue1Brown math/algorithm animations) and p5.js (browser-based generative art, shaders, interactive, 3D)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [manim, p5js, generative-art, creative-coding, animation, visualization, shaders, WebGL]
    category: creative
---

# Generative Art Coding Suite

Two engines for code-based creative visual production: **Manim CE** (Python-based math/algorithm animations, 3Blue1Brown style) and **p5.js** (browser-based generative art, interactive sketches, WebGL shaders).

**Shared creative standard**: This is visual art/cinema. Articulate creative concept BEFORE writing code. First-render excellence is non-negotiable. Cohesive aesthetic over feature count. Per-project variation — never use default configs. Invent at least one novel element per project.

---

## Mode A: Manim CE (Python, Educational Cinema)

**Trigger:** "animated explanation", "math animation", "algorithm walkthrough", "3Blue1Brown style", "equation derivation"

### Stack
Single Python script per project. Manim CE v0.20+, LaTeX, ffmpeg. No browser, no GPU required.

### Pipeline
```
PLAN → CODE → RENDER → STITCH → AUDIO (optional) → REVIEW
```

### Project Structure
```
project-name/
  plan.md        # Narrative arc, scene list, color palette
  script.py      # All scenes in one file, each independently renderable
  concat.txt     # ffmpeg scene list
  final.mp4      # Stitched output
```

### Color Palettes
| Palette | Background | Primary | Secondary | Accent |
|---------|-----------|---------|-----------|--------|
| Classic 3B1B | #1C1C1C | #58C4DD (blue) | #83C167 (green) | #FFFF00 (yellow) |
| Warm academic | #2D2B55 | #FF6B6B | #FFD93D | #6BCB77 |
| Neon tech | #0A0A0A | #00F5FF | #FF00FF | #39FF14 |
| Monochrome | #1A1A2E | #EAEAEA | #888888 | #FFFFFF |

### Key Rules
- **Geometry before algebra**: Show shape first, equation second
- **Opacity layering**: Primary 1.0, contextual 0.4, structural 0.15
- **Breathing room**: `self.wait()` after every animation
- **Use monospace fonts** for all text (Manim's Pango renderer breaks with proportional fonts)
- **Raw strings for LaTeX**: `MathTex(r"\frac{1}{2}")` — NOT `MathTex("\frac{1}{2}")`
- **buff >= 0.5 for edge text**
- **FadeOut before replacing text**: `ReplacementTransform` not `Write` on top
- **Never animate non-added mobjects**: `self.add()` first

### Render Quality
`-ql` (854x480, 15fps) for draft → `-qh` (1920x1080, 60fps) for production. Always iterate at `-ql`.

---

## Mode B: p5.js (Browser, Generative Art)

**Trigger:** "p5.js sketch", "generative art", "creative coding", "interactive visualization", "canvas animation", "browser-based visual art"

### Stack
Single self-contained HTML file per project. p5.js 1.11.3 (CDN). No build step required.

### Pipeline
```
CONCEPT → DESIGN → CODE → PREVIEW → EXPORT → VERIFY
```

### Key Rules
- **Disable FES first**: `p5.disableFriendlyErrors = true` (10x overhead otherwise)
- **Seeded randomness**: Always `randomSeed()` + `noiseSeed()` for reproducibility
- **Color mode**: Use `colorMode(HSB, 360, 100, 100, 100)` — never raw RGB
- **Noise**: Multi-octave FBM, not raw `noise(x, y)` — layer for natural texture
- **createGraphics() for layers**: Flat single-pass rendering looks flat
- **Performance**: Use `beginShape(POINTS)` or pixel buffer for thousands of particles; `Math.*` instead of p5 wrappers in hot loops
- **Headless video export**: Must use `noLoop()` in setup; capture script controls frame advance
- **Instance mode** for production (avoids `window` pollution)

### Export Patterns
| Format | Method |
|--------|--------|
| PNG | `saveCanvas('output', 'png')` in `keyPressed()` |
| GIF | `saveGif('output', 5)` |
| MP4 | Puppeteer frame capture + ffmpeg concat |
| SVG | `createCanvas(w, h, SVG)` with p5.js-svg |

### Version Notes
- **p5.js 1.x** (1.11.3): default, stable, broadest compatibility
- **p5.js 2.x**: `async setup()`, OKLCH color, `splineVertex()`, shader `.modify()`, variable fonts — required for p5.brush

---

## Shared Creative Divergence Strategies

When user requests experimental/creative/unique output:

- **Conceptual Blending**: Name two distinct visual systems, map correspondences, blend selectively
- **SCAMPER**: Substitute, Combine, Adapt, Modify, Purpose, Eliminate, Reverse known patterns
- **Forced Connections**: Pick unrelated domain, map structural elements onto visual medium
- **Oblique Strategies**: "Honor thy error as a hidden intention" / "Turn it upside down" / "Only a part"
- **Assumption Reversal**: List standard visualization assumptions, reverse the most fundamental one