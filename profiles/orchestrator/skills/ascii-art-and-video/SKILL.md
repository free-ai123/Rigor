---
name: ascii-art-and-video
description: "Generate ASCII art (pyfiglet, cowsay, boxes, image-to-ascii) and convert video/audio to colored ASCII animations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ascii, art, video, animation, pyfiglet, cowsay, terminal-art]
---

# ASCII Art & Video

## Section A: ASCII Art

Generate text-based art for terminal, code comments, or creative projects.

### Tools
- **pyfiglet** — Banner text: `pyfiglet "HELLO"` → large ASCII letters
- **cowsay** — Talking animal: `cowsay "message"`
- **boxes** — Text in decorative boxes: `echo "text" | boxes -d diamond`
- **image-to-ascii** — Convert images to ASCII art

### Usage
```bash
# Banner text
pyfiglet -f standard "Welcome"
pyfiglet -f slant "Hermes"
pyfiglet -l  # list all fonts

# Image to ASCII
# Use vision_analyze to describe the image, then generate ASCII representation
# Or use a dedicated image-to-ascii tool if installed
```

### When to Use
- Welcome banners, section dividers in terminal output
- Creative ASCII art requests
- Fun easter eggs in code
- Terminal UI decoration

## Section B: ASCII Video

Convert video or audio files to colored ASCII MP4/GIF animations.

### Usage
```bash
# Video to ASCII
# Process: extract frames → convert each to ASCII → encode as video
# Output: MP4 or GIF with colored ASCII characters
```

### When to Use
- Creative video representations
- Terminal art installations
- Novelty content
