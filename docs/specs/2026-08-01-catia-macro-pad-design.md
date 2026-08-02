# CATIA 3DX Macro Pad — Design

Date: 2026-08-01
Status: approved (chat), implemented same day

## Goal

An external control pad (its own window, outside 3DEXPERIENCE) with macro
buttons. First macro: color everything under the user's tree selection
with distinct, muted, easy-to-differentiate colors.

## Decisions (from brainstorming)

- **Pad type:** Python + tkinter desktop app, always on top; talks to the
  running session via COM (`pywin32`, `GetObject("CATIA.Application")`).
- **Scope:** whatever node(s) the user selected in the CATIA tree;
  empty selection falls back to the whole active model. Parts and
  assemblies are both handled by walking whatever children exist.
- **Coloring is hierarchical** (user requirement): hue distance mirrors
  tree distance.
  - Top-level items: clearly different muted anchor hues, extended by
    golden-angle steps when the model has more items than the curated 12.
  - Each level deeper: sibling hues confined to a window around the
    parent hue (90° below top level, ×0.4 per extra level), with sibling
    positions interleaved so tree-adjacent geosets sit far apart in hue.
  - Leaves in one container (bodies in a geoset): same hue family,
    separated by cycling saturation/lightness pairs.
  - All colors stay in a muted band (S ≈ 0.24–0.45, L ≈ 0.50–0.68).

## Structure

- `macro_pad.py` — tkinter pad; macros run on a worker thread (own COM
  init) so the UI never freezes; status bar reports results.
- `catia_pad/connection.py` — session attach with 3DX-native
  (`ActiveEditor`) and V5-style (`ActiveDocument`) fallbacks.
- `catia_pad/palette.py` — pure color math, unit-testable without CATIA.
- `catia_pad/macros/color_bodies.py` — tree walk (Products → Part →
  Bodies/HybridBodies → HybridShapes), visibility check via
  `VisProperties.GetShow`, coloring via `SetRealColor(r, g, b, 1)`.

## Error handling

Every COM access is defensive: no session / nothing open / odd document
types produce a status-bar message, never a crash. Objects whose innards
can't be enumerated (some 3DX reps) are painted whole — one color per
component is acceptable degradation. Display refresh is paused during
painting and always restored.

## Testing

`tests/test_palette.py` checks hue spread, window shrink per depth, and
muted/distinct leaf tones. The COM path needs a live 3DEXPERIENCE session
— verified manually by the user.
