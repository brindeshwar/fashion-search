# CLAUDE.md

@AGENTS.md

## Claude Code specifics

- **Preview:** `.claude/launch.json` defines `web` (`fashion-search serve`, port 8000, needs `web/dist` built) and `web-dev` (Vite, port 5173). Start them with `preview_start`, not a background Bash command. The first search after launch takes about 10 s while the model loads.
- **GPU is shared:** the user runs other GPU jobs on this machine. Check `nvidia-smi` before a real try-on, and never stop processes you didn't start; wait for them instead.
- **Shells:** the main shell is PowerShell, and the Bash tool is Git Bash. Call venv tools by path (`.venv/Scripts/pytest`) instead of activating the venv. Set `PYTHONIOENCODING=utf-8` when a script prints non-ASCII text.
- **Verifying tag or search quality:** render a contact sheet of a few images and look at it (save it to the scratchpad and Read it). Don't trust the label counts alone.
- **Memory vs docs:** project state belongs in `docs/PROGRESS.md`, not in Claude's private memory, so other agents can see it.
