# DHG Graphics Resizer — PWA

Web-based batch image resizer with DHG branding. Progressive Web App conversion of the desktop Python/tkinter application.

## Current Status: Phase 2

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Resize + Crop + 40+ Presets | ✅ Complete |
| 2 | Backgrounds + Gradients + Zip Download | ✅ Complete |
| 3 | AI Background Removal (FastAPI + rembg) | 🔲 Next |
| 4 | PWA Manifest + Service Worker + Offline | 🔲 Planned |
| 5 | Multi-workflow Comparison + Polish | 🔲 Planned |

## Features (Phase 2)

- **40+ size presets** organized by category: Headshots, Social Media Profiles, Social Media Posts, Banners & Headers, Digital Ads (IAB), Email & Web
- **3 crop modes**: Top (preserves heads in portraits), Center, Fill (no crop, pad edges)
- **Background engine**: 8 solid colors, 8 gradient presets, transparent, custom hex/gradient input
- **Gradient directions**: down, right, diagonal, radial + multi-stop
- **Export**: JPEG (50-100% quality), PNG, WebP
- **Batch download**: JSZip packages all results into a single .zip
- **DHG brand system**: Graphite #32374A, Purple #663399, Orange #F77E2D

## Quick Start

```bash
cd pwa
npm install
npm run dev
```

Open http://localhost:3000

## Docker Deployment

```bash
cd pwa
docker compose up -d
```

Access at http://localhost:3080

## Architecture

```
Browser (React + Canvas API)
├── Resize/crop: client-side Canvas
├── Gradient rendering: client-side Canvas
├── Background compositing: client-side Canvas
└── Future: API calls to FastAPI for AI bg removal

Docker Container (Phase 3)
├── FastAPI + rembg
├── BiRefNet-Portrait (blur=0.8, thresh=15, boost=1.08)
├── BiRefNet-General  (blur=1.0, thresh=20, boost=1.05)
└── BRIA RMBG         (blur=0.6, thresh=12, boost=1.10)
```

## Custom Gradient Syntax

Same as the desktop app:

| Format | Example | Result |
|--------|---------|--------|
| Solid | `#663399` | Solid purple |
| 2-color | `#663399:#F77E2D` | Top-to-bottom gradient |
| Direction | `#663399:#F77E2D:right` | Left-to-right |
| Multi-stop | `#32374A:#663399:#F77E2D` | 3-color evenly spaced |
| Radial | `#663399:#32374A:radial` | Center outward |
| Diagonal | `#F77E2D:#663399:diagonal` | Top-left to bottom-right |

## License

MIT — Digital Harmony Group
