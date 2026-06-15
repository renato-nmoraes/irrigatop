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

CSS + HTML markup restyle only. Keep the existing JavaScript behavior intact
(it already does correct AJAX for every control), keep jQuery to avoid rewrite
risk. Only two files change:

- `web/templates/index.html` — markup/structure cleanup for the new layout.
- `web/static/styles.css` — the actual restyle.

The firmware-served fallback page (`data/index.html`, `data/style.css`) is
explicitly out of scope.

## Visual design

**Direction:** evolve the current dark slate theme — same identity, tightened.

**Design tokens (CSS custom properties):**
- Background: deep slate; Surface/card: elevated slate; subtle border color.
- Accent: blue (existing `#3498db` family).
- Semantic: green = ON/online, red = OFF/offline, blue/amber = PULSE.
- Type scale, spacing scale, radius, and shadow tokens for consistency.

**Polish:** larger rounded corners, soft shadows + subtle borders for depth,
visible `:focus-visible` rings for accessibility, smooth state transitions.

## Layout (single centered column, mobile-first, max-width ~480px)

1. **Header** — "IrrigaTOP" title bar.
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
   viewport.

## Out of scope

- Backend/`app.py` changes.
- Firmware and `data/` fallback page.
- Credential/secret handling (covered by a separate prior pass).
- Replacing jQuery or any dependency changes.
