# telegram-history-export storage

Source code stays in this repository. The default sibling PRIVATE companion is
`../telegram-history-export-config`. An explicit `TELEGRAM_HISTORY_EXPORT_CONFIG`
selects another root; with neither, the tools stop with initialization guidance. Real records, credentials and recovery history belong
in a versioned PRIVATE companion, never a public or unknown-visibility source tree.

The companion preserves the existing file names and schemas, with `data/` reserved
for recovered outputs. Key files and sessions retain their original semantics.
The tool does not automatically log in, export, decrypt or consume a queue during
directory maintenance. Restore does not overwrite original message databases.

Keep keys, sessions, restored message evidence and the source schema together in
private version history. Rebuildable caches and failed temporary outputs may be
reviewed separately. `storage.contract.json` lists this preservation scope.

Path selection uses the companion resolver of the installed fleet_guards package (`pip install -e "$(git config --get fleet.guards)"`). Credential writers use the same `config_root()` as readers: when no companion resolves it raises with restore guidance, and nothing falls back into this repository. No privacy proof runs at write time; the commit and push hooks keep DATA out of the public repository. Explicit overrides must be absolute; canonical source aliases are rejected.
