## MODIFIED Requirements

### Requirement: Storage layout
The system SHALL keep everything about one video in a project directory `data/projects/<name>/`: the video file, a
`project.json` with the project name, the video file name and the title used as metadata (default: the video file
stem), all processing results, the eval set `eval.json` and generated reports. The data root SHALL be overridable via
`OVU_HOME`.

#### Scenario: Results directory derived from the file name
- **WHEN** a step processes project `my-video`
- **THEN** it reads the video named in `data/projects/my-video/project.json` and writes its results into
  `data/projects/my-video/`

### Requirement: Video references
Commands taking a video SHALL accept a project name, or a substring that matches exactly one project name; otherwise
they SHALL fail and list the projects.

#### Scenario: Partial slug
- **WHEN** the user runs `ovu app talk` and exactly one project name contains `talk`
- **THEN** that project is used

#### Scenario: Ambiguous slug
- **WHEN** the given text matches several projects or none
- **THEN** the command exits with an error listing the project names

### Requirement: Download from URL
The system SHALL download a video from a URL with yt-dlp into a project directory as MP4 (at most 1080p), using node
as JavaScript runtime when available and, if requested, the cookies of a named local browser.

#### Scenario: YouTube video with browser cookies
- **WHEN** the user runs `ovu new my-video <youtube-url> --cookies-from chrome`
- **THEN** the merged MP4 is saved in `data/projects/my-video/` and recorded in `project.json`

#### Scenario: Download refused
- **WHEN** yt-dlp fails
- **THEN** the command exits with the end of yt-dlp's error output and a hint to try `--cookies-from`, and no
  project is left behind

## ADDED Requirements

### Requirement: Project creation
`ovu new <name> <file-or-url>` SHALL create the project directory, copy a local video file into it (or download a
URL) and write `project.json`; it SHALL refuse an existing project name and names that are not lower-case
letters, digits and `-`. An optional `--title` SHALL override the title metadata.

#### Scenario: Local file
- **WHEN** the user runs `ovu new my-video ~/Downloads/clip.mp4`
- **THEN** `data/projects/my-video/clip.mp4` is a copy of the file and `project.json` names it

#### Scenario: Existing name
- **WHEN** a project `my-video` already exists
- **THEN** `ovu new my-video ...` fails without changing it
