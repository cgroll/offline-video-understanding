## 1. Project layout

- [x] 1.1 `paths.py`: `data/projects/<name>/`, `project.json` read/write, resolve a project by name or unique substring,
  list projects; result directory and eval file derived from the project
- [x] 1.2 `ovu new <name> <file-or-url> [--title] [--cookies-from]`: validate the name, copy or download the video,
  write `project.json`, clean up on failed download
- [x] 1.3 `download.py`: download into a given directory and return the file

## 2. Language per project

- [x] 2.1 `language.py`: store language and source in `project.json` instead of `meta.json`
- [x] 2.2 explicit language different from the stored one deletes generated texts, reports and the `caption`,
  `caption_ctx`, `chapter` embeddings

## 3. CLI and docs

- [x] 3.1 `ovu list` shows title, language and results per project; `process` takes a project; eval reads
  `eval.json` and fails clearly when it is missing
- [x] 3.2 update README, PROJECT.md, AGENTS.md, eval/README.md (moved to docs of `eval.json`), `.gitignore`

## 4. Migration and check

- [x] 4.1 create the two local projects from the existing videos and results (manual, not committed)
- [x] 4.2 check `ovu list`, `ovu eval` and `ovu app` on a migrated project; eval numbers unchanged
