## ADDED Requirements

### Requirement: Playback speed
The player SHALL offer the speeds 1×, 1.5× and 2× as a toggle in the player bar and via the keys `<` and `>`,
SHALL show the active speed, and SHALL restore the last chosen speed when the GUI is opened again in the same browser.

#### Scenario: Faster playback
- **WHEN** the user clicks 2× or presses `>` twice from 1×
- **THEN** the video plays at double speed, 2× is highlighted, and timeline and transcript stay in sync

#### Scenario: Speed remembered
- **WHEN** the user chose 1.5× and reloads the page
- **THEN** the video starts at 1.5×
