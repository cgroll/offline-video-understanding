## 1. CLI

- [x] 1.1 `ovu process`: replace `--no-vlm` by `--vlm`; without it run transcription and the non-VLM embedding
  variants only; `--language` without `--vlm` only stores the language
- [x] 1.2 the final embedding pass computes VLM-based variants only when their inputs exist (unchanged behaviour of
  `embed.run(None)`)

## 2. Docs

- [x] 2.1 README, PROJECT.md, AGENTS.md: default pipeline without VLM, `--vlm` for descriptions, chapters and report

## 3. Check

- [x] 3.1 `ovu process <project>` on an already processed project skips everything and loads no VLM
- [x] 3.2 `openspec validate --strict`
