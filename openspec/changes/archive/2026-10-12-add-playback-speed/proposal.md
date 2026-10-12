## Why

Reviewing search results often means watching longer passages. The browser's own speed menu is hidden in the video
controls, so faster playback should be one click (or key) away in the player bar.

## What Changes

- Speed toggle **1× · 1.5× · 2×** in the player bar next to the "Similar to" button.
- Keys `<` and `>` step the speed down and up; the active button reflects speed changes from any source (including
  the browser's own menu).
- The chosen speed is remembered per browser and restored when the GUI opens; without browser storage it starts
  at 1×.

## Capabilities

### New Capabilities

### Modified Capabilities
- `search-gui`: playback speed control in the player

## Impact

- Only `src/ovu/app/index.html`; no backend, pipeline or model change. No VRAM or runtime impact, and no effect on
  eval metrics (UI only).
- Timeline, playhead and transcript sync use `currentTime` and keep working at any speed.
