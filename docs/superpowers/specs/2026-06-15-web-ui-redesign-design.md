# IrrigaTOP Web UI Redesign — Design

**Date:** 2026-06-15
**Scope:** Visual restyle of the Flask web app UI only (`web/`). No backend,
endpoint, or behavior changes.

## Goal

The web control panel works but looks basic. Give it a polished "refined dark
dashboard" look while preserving every existing behavior and the backend
contract. This is an aesthetic pass, not a feature change.

## Hard constraints (must not break)

These are the crucial rules carried over from the current app:

1. **No page reloads / no navigation.** Every control updates in place via AJAX.
   The 0–100 intensity slider and number box must never trigger a reload (this
   was an early bug and must stay fixed).
2. **Backend contract unchanged:** routes `/`, `/status`, `/health`,
   `/intensity`, `/pump` and form field names `action`, `slider`, `pump_id`
   stay exactly as they are.
3. **Same controls and copy:** pump 1/2 selection, ON / OFF / PULSE actions,
   intensity 0–100, live status + connection polling (every 5s), Portuguese
   labels, the "IrrigaTOP" name.

## Approach

CSS + HTML markup restyle. Keep the existing control JavaScript behavior intact
(it already does correct AJAX for every control), keep jQuery to avoid rewrite
risk. The only new JS is a small, self-contained theme-init/toggle script that
sets `data-theme` and persists the choice — it does not touch the control flow.
Only two files change:

- `web/templates/index.html` — new markup/layout + theme toggle + init script.
- `web/static/styles.css` — the restyle and themed CSS variables.

The firmware-served fallback page (`data/index.html`, `data/style.css`) is
explicitly out of scope.

## Visual design

**Direction: "Botanical Calm."** A calm, organic, premium feel suited to a
device that keeps living things alive — not a generic admin panel. Validated
against rendered prototypes (light + dark).

**Typography:**
- Display: **Fraunces** (organic optical serif) for the wordmark and the
  oversized intensity numeral (the signature moment).
- UI/body: **Hanken Grotesk**.
- Loaded via Google Fonts `<link>`. Font stacks MUST include graceful fallbacks
  (`Georgia, serif` for display; `system-ui, sans-serif` for body) so the layout
  still works if the webfonts fail to load. (Self-hosting the two fonts under
  `web/static/fonts/` is a recommended future hardening to drop the external
  dependency.)

**Palette (CSS custom properties, themed):**
- Light: warm paper `#efece3` bg, card `#f8f6f0`, forest-green ink `#1c2a22`,
  primary green `#2e7d52` / bright `#46a86e`, terracotta `#bb6240` for OFF
  (instead of harsh red, to keep the palette harmonious).
- A soft green radial glow bleeds from the top; a faint SVG grain texture adds
  warmth.

**Polish:** generous whitespace, hairline borders, restrained rounded corners,
editorial status sentence ("A bomba está *ligada*"), eyebrow micro-labels on the
action buttons, leaf wordmark glyph, subtle dark pill toast, visible
`:focus-visible` rings for accessibility.

## Theme toggle (light / dark)

- A sun/moon icon button in the header toggles between light and the dark
  "Botanical Calm" variant (warm green-black bg `#0f1613`, brighter green
  `#4fae74`, off-white ink `#e9ece4`; grain blends via `screen` on dark).
- Implementation: the toggle flips a `data-theme` attribute on `<html>`; all
  colors are CSS variables overridden under `[data-theme="dark"]`, so switching
  is instant and CSS-only.
- Default: respect `prefers-color-scheme`. Persist the user's explicit choice in
  `localStorage` (`irrigatop-theme`). A tiny init script sets the attribute on
  load. This is purely client-side and does NOT touch the MQTT/AJAX flow or
  cause a reload.

## Layout (single centered column, mobile-first, max-width ~480px)

1. **Header** — leaf wordmark "IrrigaTOP" (left); theme toggle + an "Online"
   connection chip (right).
2. **Pump selector** — segmented toggle `Bomba 1 | Bomba 2` (replaces the custom
   `<div>` dropdown). One tap; removes the fragile click-outside-to-close JS.
   Still POSTs `pump_id` to `/pump` identically. The active segment is
   highlighted.
3. **Status card** — one elevated card containing:
   - Pump status as a color-coded pill (ON=green, OFF=red, PULSE=blue), driven
     by `/status` polling.
   - Connection indicator dot (online/offline), driven by `/health` polling.
4. **Action buttons** — ON / OFF / PULSE with larger tap targets and clear
   hover / active / disabled / pressed states. The button matching the current
   status is visually marked active.
5. **Intensity** — slider + number box side by side, kept in sync, with the
   existing live gradient fill. Same debounced AJAX POST to `/intensity`.
6. **Toasts** — existing success/error notification, restyled.

## Components and their contracts

| Component | Behavior (unchanged) | Restyle |
|-----------|----------------------|---------|
| Pump selector | `POST /pump` with `pump_id` (1\|2) | dropdown → segmented toggle |
| Action buttons | `POST /` with `action` (ON/OFF/PULSE), AJAX | bigger, stateful styling |
| Intensity | `POST /intensity` with `slider` (0–100), debounced AJAX | synced slider+number, gradient fill |
| Status pill | `GET /status` poll every 5s | color-coded pill |
| Connection dot | `GET /health` poll every 5s | online/offline dot |
| Toast | client-side only | restyled success/error |
| Theme toggle | new, client-side only (`data-theme` + localStorage) | sun/moon button |

## Error handling

Unchanged from current behavior: failed AJAX calls surface the existing toast
notification ("Failed to …"); polling failures mark the connection dot offline.
No new error paths introduced.

## Testing

1. **Endpoint/contract regression** — rebuild the web container against a local
   Mosquitto broker (existing Docker harness) and confirm: `/` returns 401
   without basic auth; an `action=ON` POST publishes `ON` to `irrigation/action`;
   `/status`, `/health`, `/intensity` (`slider`), `/pump` (`pump_id`) all
   respond success. This proves the field names and routes are intact.
2. **No-reload check** — confirm the rendered page issues XHRs (not navigations)
   for slider, number box, buttons, and pump toggle; no full reload occurs.
3. **Visual check** — render the page and verify layout on a narrow (mobile)
   viewport, in both light and dark themes.
4. **Theme toggle check** — toggling flips `data-theme`, persists to
   `localStorage`, defaults from `prefers-color-scheme`, and causes no reload.

## Out of scope

- Backend/`app.py` changes.
- Firmware and `data/` fallback page.
- Credential/secret handling (covered by a separate prior pass).
- Replacing jQuery or any dependency changes.
