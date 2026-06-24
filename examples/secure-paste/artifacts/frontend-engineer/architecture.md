# Frontend Architecture: SecurePaste

**Date**: 2026-06-24  
**Author**: Frontend Engineer (AI)

## Tech Stack

- **Vanilla HTML/JS**: To minimize bundle size and avoid dependency risks
- **Highlight.js**: Client-side syntax highlighting
- **CSS Variables**: For easy theming (Dark Mode default)

## Component Structure

```
SecurePaste UI
├── Create Mode (Home)
│   ├── Content Input (Monospace Textarea)
│   ├── Options Panel (Expiration, Password)
│   ├── Burn Toggle (Checkbox)
│   └── Result Area (Generated Link)
└── View Mode (/p/{id})
    ├── Password Modal (Overlay)
    ├── Code Display Block (Syntax Highlighted)
    ├── Meta Info (Expiration, Burn status)
    └── Burned State (Warning message)
```

## Security Considerations

1. **No Local Storage**: Sensitive content is never stored in browser storage
2. **Clipboard API**: Used securely for copying content
3. **CORS**: Strict CORS policy applied to API endpoints
4. **Content Sanitization**: All content rendered as text, never innerHTML

## File List

- `index.html`: Single Page Application (SPA)
