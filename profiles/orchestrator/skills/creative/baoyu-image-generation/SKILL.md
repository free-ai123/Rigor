---
name: baoyu-image-generation
description: "Baoyu image generation suite: article illustrations, knowledge comics, infographics. Type × Style × Palette consistency via image_generate."
version: 1.0.0
author: 宝玉 (JimLiu), adapted for Hermes
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [article-illustration, comic, infographic, creative, image-generation]
    category: creative
---

# Baoyu Image Generation Suite

Three illustration modes sharing a common workflow: **analyze → confirm → generate prompts → call image_generate → download → finalize**. All use Hermes' `image_generate` tool (prompt-only, returns URL, must download).

## Common Patterns (apply to ALL modes)

### image_generate Behavior
- Accepts only `prompt` (text) and `aspect_ratio` (`landscape` | `portrait` | `square`)
- Returns a URL, NOT a local file — **always download via `terminal`** (`curl -fsSL "<url>" -o "<abs-path>"`)
- **Use absolute paths for `curl -o`** — never rely on persistent-shell CWD across batches
- On generation failure, auto-retry once
- Aspect ratio mapping: `16:9` → `landscape`, `9:16` → `portrait`, `1:1` → `square`

### Prompt File Requirement (hard)
Every image must have a saved prompt file under `prompts/` BEFORE calling `image_generate`. The prompt file is the reproducibility record.

### Clarify Protocol
Since `clarify` handles one question at a time, ask the most important question first. Don't call `clarify` more than 2-3 times in a row. Skip questions already answered by the user's request.

### Timeout Handling
If `clarify` times out, treat it as a default for that one question only. Surface the default to the user visibly so they can correct it.

### Backup Rule
If output files (`source.md`, `analysis.md`, `prompts/…`) already exist, rename with `-backup-YYYYMMDD-HHMMSS` suffix before regenerating.

### Data Integrity
Never summarize, paraphrase, or alter source statistics. Strip secrets/credentials before writing output files.

### Language Handling
Detection priority: user-specified > conversation language > source content language. Use detected language for all interactions (outlines, prompts, updates, summaries).

---

## Mode A: Article Illustrator

**Trigger:** "illustrate article", "为文章配图", "add images to content"
**Output:** Multiple illustrations embedded in an article, with type × style × palette consistency.

### Three Dimensions
| Dimension | Controls | Values |
|-----------|----------|--------|
| **Type** | Information structure | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | Rendering approach | notion, warm, minimal, blueprint, watercolor, elegant |
| **Palette** | Color scheme | macaron, warm, neon (optional, overrides style defaults) |

Presets available: `edu-visual` → type + style + palette in one shot.

### Core Principles
- **Visualize concepts, not metaphors** — illustrate the underlying concept, not literal images
- **Labels use article data** — actual numbers, terms, quotes from the article
- **Prompt files are mandatory** — saved under `prompts/` before any generation

### Workflow
1. Detect reference images (if provided) → `vision_analyze` → record in `{output-dir}/references/`
2. Analyze content → `{output-dir}/analysis.md`
3. Confirm settings via `clarify`: [Preset/Type] → [Density] → [Style] → [Palette]
4. Generate outline → `{output-dir}/outline.md` with frontmatter and per-illustration entries
5. Generate prompts → `{output-dir}/prompts/NN-{type}-{slug}.md` (BLOCKING: all prompts before images)
6. Generate images → `image_generate(prompt=...)` → download URL to `{output-dir}/NN-{type}-{slug}.png`
7. Finalize → insert `![desc](imgs/NN-{type}-{slug}.png)` after corresponding paragraph

### Output Structure
```
{output-dir}/
├── source-{slug}.{ext}    # Only for pasted content
├── analysis.md
├── outline.md
├── prompts/
│   └── NN-{type}-{slug}.md
└── NN-{type}-{slug}.png
```

Default output dir: `{article-dir}/imgs/` for file input, `illustrations/{topic-slug}/` for pasted content.

### Modification
| Action | Steps |
|--------|-------|
| Edit | Update prompt → Regenerate → Update reference |
| Add | Position → Prompt → Generate → Update outline → Insert |
| Delete | Delete files → Remove reference → Update outline |

### Pitfalls
- Data integrity is paramount — never alter source statistics
- Don't illustrate metaphors literally
- `image_generate` aspect ratios: only `landscape`, `portrait`, `square`
- No backend selection from agent — `image_generate` uses user-configured model

---

## Mode B: Knowledge Comic (知识漫画)

**Trigger:** "knowledge comic", "educational comic", "biography comic", "tutorial comic", "知识漫画"
**Output:** Multi-page knowledge comic with consistent characters across pages.

### Options
| Option | Values |
|--------|--------|
| Art | ligne-claire (default), manga, realistic, ink-brush, chalk, minimalist |
| Tone | neutral (default), warm, dramatic, romantic, energetic, vintage, action |
| Layout | standard (default), cinematic, dense, splash, mixed, webtoon, four-panel |
| Aspect | 3:4 (default), 4:3, 16:9 |
| Language | auto, zh, en, ja, etc. |

### Presets
| Preset | Equivalent | Hook |
|--------|-----------|------|
| `ohmsha` | manga + neutral | Visual metaphors, no talking heads, gadget reveals |
| `wuxia` | ink-brush + action | Qi effects, combat visuals, atmospheric |
| `shoujo` | manga + romantic | Decorative elements, eye details |
| `concept-story` | manga + warm | Visual symbol system, growth arc |
| `four-panel` | minimalist + neutral + four-panel | 起承转合, B&W + spot color |

### File Structure
```
comic/{topic-slug}/
├── source-{slug}.md
├── analysis.md
├── storyboard.md
├── characters/
│   ├── characters.md        # Text definitions (embedded in every page prompt)
│   └── characters.png       # Human-facing review artifact only
├── prompts/
│   └── NN-{cover|page}-{slug}.md
└── NN-{cover|page}-{slug}.png
```

### Workflow
1. Analyze content → `analysis.md`, `source-{slug}.md`
2. **Confirm style + options via `clarify`** (REQUIRED — do not skip)
3. Generate storyboard + characters → `storyboard.md`, `characters/characters.md`
4. Generate prompts → `prompts/NN-{cover|page}-{slug}.md` (character descriptions embedded inline)
5. Generate character sheet (if needed) → `characters/characters.png` (aspect `landscape`)
6. Generate pages → `image_generate` per page → download each PNG
7. Completion report

### Character Consistency
Driven by **text descriptions** in `characters/characters.md` embedded inline in every page prompt during Step 4. The PNG sheet is a review artifact only — `image_generate` cannot accept images as visual input.

### Partial Workflows
- Storyboard only / Prompts only / Images only / Regenerate N — see full workflow for details.

### Pitfalls
- Step 2 confirmation is required
- Always download `image_generate` URLs to local PNGs
- Use absolute paths for `curl -o` — CWD can drift between terminal batches
- Strip secrets from source content
- Existing prompt/PNG files → rename with `-backup-YYYYMMDD-HHMMSS` before regenerating

---

## Mode C: Infographic (信息图 / 可视化)

**Trigger:** "infographic", "visual summary", "信息图", "可视化", "高密度信息大图"
**Output:** Single infographic with layout × style combination.

### Two Dimensions: Layout × Style
Combine any layout with any style (21 × 21 combinations).

**Layouts** (21): linear-progression, binary-comparison, comparison-matrix, hierarchical-layers, tree-branching, hub-spoke, structural-breakdown, bento-grid (default), iceberg, bridge, funnel, isometric-map, dashboard, periodic-table, comic-strip, story-mountain, jigsaw, venn-diagram, winding-roadmap, circular-flow, dense-modules

**Styles** (21): craft-handmade (default), claymation, kawaii, storybook-watercolor, chalkboard, cyberpunk-neon, bold-graphic, aged-academia, corporate-memphis, technical-schematic, origami, pixel-art, ui-wireframe, subway-map, ikea-manual, knolling, lego-brick, pop-laboratory, morandi-journal, retro-pop-grid, hand-drawn-edu

### Keyword Shortcuts
| User Keyword | Layout | Recommended Styles |
|--------------|--------|--------------------|
| 高密度信息图 / high-density-info | `dense-modules` | morandi-journal, pop-laboratory, retro-pop-grid |
| 信息图 / infographic | `bento-grid` | craft-handmade |

### Output Structure
```
infographic/{topic-slug}/
├── source-{slug}.{ext}
├── analysis.md
├── structured-content.md
├── prompts/infographic.md
└── infographic.png
```

### Workflow
1. Analyze content → `analysis.md`, `source.md`
2. Generate structured content → `structured-content.md` (learning objectives, sections, data points)
3. Recommend 3-5 layout×style combinations based on data structure and content tone
4. Confirm via `clarify`: [Combination] → [Aspect] → [Language]
5. Generate prompt → `prompts/infographic.md` (combine layout def + style def + base template + structured content)
6. Generate image → `image_generate` → download
7. Output summary

### Pitfalls
- Data integrity is paramount
- Style consistency — don't mix styles within one infographic
- One message per section — don't overload sections
- `image_generate` aspect ratios: map custom ratios to nearest named option

---

## Common Reference Files (in subdirectories)

All mode-specific reference docs, templates, and layout/style definitions live in the skill's `references/` directory:
- `references/illustrator-workflow.md` — Article illustrator detailed procedures
- `references/illustrator-styles.md` — Style gallery + palette gallery + presets
- `references/comic-workflow.md` — Comic detailed workflow, retry handling, partial workflows
- `references/comic-art-styles/` — Art style definitions (ligne-claire, manga, etc.)
- `references/comic-tones/` — Tone definitions (neutral, warm, etc.)
- `references/comic-presets/` — Preset rules (ohmsha, wuxia, etc.)
- `references/infographic-layouts/` — 21 layout definitions
- `references/infographic-styles/` — 21 style definitions
- `references/shared-prompt-construction.md` — Prompt construction patterns common to all modes