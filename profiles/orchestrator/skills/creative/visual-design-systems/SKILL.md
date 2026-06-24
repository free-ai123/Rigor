---
name: visual-design-systems
description: "Visual design: DESIGN.md token specs (Google), Excalidraw diagrams, and 54 real-world web design systems as HTML/CSS templates."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, design-system, tokens, excalidraw, diagrams, web-design, css, ui]
    category: creative
---

# Visual Design Systems Suite

Three visual design tools: formal token specs, hand-drawn diagrams, and production-ready web design templates.

---

## Mode A: DESIGN.md Token Specs (Google)

**Trigger:** "DESIGN.md", "design tokens", "design system spec", "WCAG contrast", "token spec"

DESIGN.md is Google's open spec (Apache-2.0) for describing visual identity to coding agents. One file combines YAML front matter (machine-readable tokens) + Markdown body (human-readable rationale).

### Token Types
| Type | Format | Example |
|------|--------|---------|
| Color | `#` + hex (sRGB) | `"#1A1C1E"` |
| Dimension | number + unit | `48px`, `-0.02em` |
| Token reference | `{path.to.token}` | `{colors.primary}` |
| Typography | object with fontFamily, fontSize, fontWeight, lineHeight, letterSpacing | see below |

### Canonical Section Order
1. Overview → 2. Colors → 3. Typography → 4. Layout → 5. Elevation & Depth → 6. Shapes → 7. Components → 8. Do's and Don'ts

### CLI (npx, no install)
```bash
npx -y @google/design.md lint DESIGN.md                    # Validate + WCAG contrast
npx -y @google/design.md diff DESIGN.md DESIGN-v2.md       # Compare, fail on regression
npx -y @google/design.md export --format tailwind DESIGN.md > tailwind.theme.json
npx -y @google/design.md export --format dtcg DESIGN.md > tokens.json
```

### Pitfalls
- Don't nest component variants: `button-primary-hover` (sibling key), NOT `button-primary.hover`
- Hex colors must be quoted strings in YAML
- Negative dimensions need quotes: `letterSpacing: "-0.02em"`
- Token references resolve by dotted path: `{colors.primary}` works, `{primary}` does not

---

## Mode B: Excalidraw Diagrams

**Trigger:** "diagram", "architecture diagram", "flowchart", "sequence diagram", "excalidraw"

Create diagrams by writing standard Excalidraw element JSON and saving as `.excalidraw` files. Drag-and-drop onto excalidraw.com for viewing.

### Element Types
Rectangle, Ellipse, Diamond, Arrow, Text (standalone or bound to shapes).

### Key Rules
- **Labeled shapes**: Use container binding (shape has `boundElements`, text has `containerId`) — NOT `"label"` on shapes
- **Drawing order**: Array order = z-order. Emit: bg → shape → its bound text → its arrows → next shape
- **Font sizes**: Minimum 16 for body, 20 for titles, 14 for annotations only. NEVER below 14
- **Text positioning**: `x` is LEFT edge. To center at `cx`: `x = cx - (text.length * fontSize * 0.5) / 2`
- **Arrow bindings**: `startBinding: { elementId: "r1", fixedPoint: [1, 0.5] }` for shape-attached arrows
- **No emoji in text** — doesn't render in Excalidraw's font
- **Text contrast**: Never light gray on white. Minimum `#757575`

### Color Palette (quick reference)
| Use | Fill | Hex |
|-----|------|-----|
| Primary/Input | Light Blue | `#a5d8ff` |
| Success/Output | Light Green | `#b2f2bb` |
| Warning/External | Light Orange | `#ffd8a8` |
| Processing | Light Purple | `#d0bfff` |
| Error | Light Red | `#ffc9c9` |
| Notes | Light Yellow | `#fff3bf` |
| Storage/Data | Light Teal | `#c3fae8` |

---

## Mode C: Popular Web Designs (54 Design Systems)

**Trigger:** "build a page that looks like", "Stripe style", "Linear design", "Vercel style", "landing page"

54 real-world design systems ready for HTML/CSS generation. Each template captures a site's complete visual language: color palette, typography, components, spacing, shadows, responsive behavior.

### Categories
- **AI & ML:** Claude, Cohere, ElevenLabs, Mistral, Ollama, Replicate, RunwayML, xAI
- **Dev Tools:** Cursor, Expo, Linear, PostHog, Raycast, Sentry, Supabase, Vercel, Warp
- **Infrastructure:** ClickHouse, HashiCorp, MongoDB, Sanity, Stripe
- **Design/Productivity:** Airtable, Figma, Framer, Miro, Notion, Webflow
- **Fintech:** Coinbase, Kraken, Revolut, Wise
- **Enterprise/Consumer:** Airbnb, Apple, BMW, IBM, NVIDIA, SpaceX, Spotify, Uber

### Font Substitution (proprietary → CDN)
| Proprietary | CDN Substitute |
|-------------|----------------|
| Geist / Geist Sans | Geist (Google Fonts) |
| sohne-var (Stripe) | Source Sans 3 |
| Berkeley Mono | JetBrains Mono |
| Circular (Spotify) | DM Sans |
| figmaSans | Inter |
| IBM Plex | IBM Plex (on Google Fonts) |

### HTML Generation Pattern
1. Pick design from catalog
2. Load template: `skill_view(name="popular-web-designs", file_path="templates/<site>.md")`
3. Apply CDN font `<link>`, CSS custom properties for colors, typography, component styles
4. Write with `write_file`, serve via cloudflared tunnel, verify with `browser_vision`

### Choosing a Design
Match design to content: dev tools → Linear/Vercel/Supabase; docs → Mintlify/Notion; marketing → Stripe/Framer/Apple; dark mode → Linear/Cursor/ElevenLabs; light/clean → Vercel/Stripe/Notion.