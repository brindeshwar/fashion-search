# CLAUDE.md

@AGENTS.md

## Claude Code specifics

- **Preview:** `.claude/launch.json` defines the `fashion-search` server on port 7860. Start it with `preview_start`, not a background Bash command. The first search after launch takes about 10 s while the model loads.
- **Shells:** the main shell is PowerShell, and the Bash tool is Git Bash. Call venv tools by path (`.venv/Scripts/pytest`) instead of activating the venv. Set `PYTHONIOENCODING=utf-8` when a script prints non-ASCII text.
- **Verifying tag or search quality:** render a contact sheet of a few images and look at it (save it to the scratchpad and Read it). Don't trust the label counts alone.
- **Memory vs docs:** project state belongs in `docs/PROGRESS.md`, not in Claude's private memory, so other agents can see it.
