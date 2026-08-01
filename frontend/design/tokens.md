# Kavach Design Tokens

Phase 01A — single source of truth for colors, typography, spacing, and radius. **Never hardcode a hex value in a component file** — every color traces back to a token defined here and exported via `index.css` `@theme` (Tailwind v4 CSS-first config).

## Color tokens

All tokens live in `frontend/src/index.css` under `@theme`. Use them in CSS via `var(--color-name-shade)` or in className via the Tailwind v4-generated utility (e.g. `bg-primary-500`, `text-success-600`).

### Neutrals (zinc-based, theme-aware)

| Token | Light | Dark | Semantic var | Tailwind utility |
|---|---|---|---|---|
| background | `#FAFAFA` | `#09090B` | `--background` | `bg-background` |
| surface (cards/panels) | `#FFFFFF` | `#18181B` | `--card` | `bg-card` |
| border | `#E4E4E7` | `#27272A` | `--border` | `border-border` |
| text-primary | `#18181B` | `#FAFAFA` | `--foreground` | `text-foreground` |
| text-secondary | `#71717A` | `#A1A1AA` | `--muted-foreground` | `text-muted-foreground` |

Theme is class-based — `:root` defaults to dark; `.light` switches to light variables. The `dark:` Tailwind variant is **not** used; theme switching is done by toggling the `.light` class on `<html>`.

### Brand & status (single-palette, identical in both themes)

| Token | Hex | Use |
|---|---|---|
| `--color-primary-500` (brand) | `#6366F1` | Primary actions, links, focus rings |
| `--color-primary-600` | `#4F46E5` | Primary hover/active |
| `--color-accent-500` (violet) | `#8B5CF6` | Secondary accent, design-phase branding |
| `--color-success-500` | `#10B981` | Approved, active, healthy trust |
| `--color-warning-500` | `#F59E0B` | Escalated, elevated risk, dropping trust |
| `--color-danger-500` | `#EF4444` | Denied, revoked, kill switch, tampered audit |
| `--color-info-500` | `#0EA5E9` | Informational, neutral highlights |

Each status token ships with a 400 (lighter) and 600 (darker) companion for hover/disabled gradients — see `index.css` for the full ramp (50–900 for primary, 400–600 for status).

### Surface ramp (zinc)

`--color-surface-50` through `--color-surface-950` — explicit ramp so components can pick e.g. `surface-800` for an inset panel without a theme switch.

## Typography

| Token | Family | Use |
|---|---|---|
| `--font-sans` | Inter (400/500/600/700/800) | All UI text |
| `--font-mono` | JetBrains Mono (400/500/600) | **Data, never prose** — agent IDs, hashes, JSON, timestamps, code |

**Rule:** never render a UUID, hash, or timestamp in the sans font. The monospace switch is itself a usability signal ("this is copyable data"). Use Tailwind's `font-mono` utility.

Loaded via `index.html` (Google Fonts) — Inter variable weights and JetBrains Mono.

## Spacing & radius

Tailwind's default 4px-base spacing scale is used unchanged. Radius tokens:

| Use | Value | Tailwind utility |
|---|---|---|
| Card / panel | 12px | `rounded-xl` |
| Button / input | 8px | `rounded-lg` |
| Pill / badge | 9999px | `rounded-full` |

## Shadow scale

| Use | Tailwind utility |
|---|---|
| Resting cards | `shadow-sm` |
| Hover / focus only | `shadow-md` |

Never use heavy drop shadows (`shadow-lg` and above) — they read as dated, not modern.

## Layout

| Token | Value | Use |
|---|---|---|
| `--sidebar-width` | 260px | Expanded sidebar |
| `--sidebar-collapsed-width` | 68px | Collapsed sidebar |
| `--topbar-height` | 56px | Authenticated app top bar |

## Risk-score badge color convention (Phase 01C — binding)

This is the **canonical** mapping reused by the transaction feed, audit log, and agent detail screens. Defined in `frontend/src/components/ui/risk-badge.jsx` and re-exported from `@/mocks/livedata`:

| Risk score range | Level | Color token | Badge variant |
|---|---|---|---|
| 0 – 29 | Low | `--color-success-500` | `success` |
| 30 – 59 | Mid | `--color-warning-500` | `warning` |
| 60 – 84 | High | `--color-danger-400` | `danger` |
| 85 – 100 | Critical | `--color-danger-500` | `danger` |

Note: Phase 03's live feed uses `warning` for both Low and Mid scores in *the scrolling row* (semantic green doesn't pop in a fast-scrolling list), but the **canonical, exported** mapping above is what Phase 04's audit log and policy screens reuse — never invent a new threshold per screen.

## Animations (utility classes in `index.css`)

| Class | Purpose |
|---|---|
| `animate-shimmer` | Skeleton loading (gradient sweep) |
| `animate-pulse-ring` | Graph node live-pulse ring |
| `animate-fade-in` | Generic entrance |
| `animate-slide-in-left` | Sidebar / slide-over entrance |
| `animate-number-pop` | AnimatedCounter value tick |
| `animate-node-pulse` | Soft graph-node pulse |
| `stagger-children` | Staggered list entrance (8 children max) |
