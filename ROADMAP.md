# Roadmap

- Incremental export: only pull messages newer than the last run, keyed by message id per dialog.
- HTML output beside JSON, matching the sibling discord and qq history tools.
- Media export (photos, voice, files) with local references, off by default.
- Resolve sender ids to a stable per-conversation pseudonym in the output, without storing names.
- A small orchestrator shared across the discord, qq, and telegram history tools.
