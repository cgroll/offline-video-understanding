# video-library Specification

## Purpose
Store videos and their processing results in a predictable layout, and acquire videos from URLs, so that every
pipeline step can find its inputs and outputs by the video's slug.

## Requirements

### Requirement: Storage layout
The system SHALL store source videos in `data/videos/`, all results of a video in `data/processed/<slug>/`, and
evaluation queries in `eval/<slug>.json`, where `<slug>` is the lower-cased file stem with every run of
non-alphanumeric characters replaced by `-`. The project root SHALL be overridable via `OVU_HOME`.

#### Scenario: Results directory derived from the file name
- **WHEN** a step processes `data/videos/My Video ｜ Part 1.mp4`
- **THEN** it reads and writes files in `data/processed/my-video-part-1/`

### Requirement: Video references
Commands taking a video SHALL accept either a path to a video file or a partial slug that matches exactly one video
in `data/videos/`; otherwise they SHALL fail and list the candidates.

#### Scenario: Partial slug
- **WHEN** the user runs `ovu app part-1` and exactly one video slug contains `part-1`
- **THEN** that video is used

#### Scenario: Ambiguous slug
- **WHEN** the given text matches several videos or none
- **THEN** the command exits with an error listing the candidate slugs

### Requirement: Download from URL
The system SHALL download a video from a URL with yt-dlp into `data/videos/` as MP4 (at most 1080p), using node as
JavaScript runtime when available and, if requested, the cookies of a named local browser.

#### Scenario: YouTube video with browser cookies
- **WHEN** the user runs `ovu download <youtube-url> --cookies-from chrome`
- **THEN** the merged MP4 is saved under its title in `data/videos/` and its path is printed

#### Scenario: Download refused
- **WHEN** yt-dlp fails
- **THEN** the command exits with the end of yt-dlp's error output and a hint to try `--cookies-from`
