# Working on this repository

Keep changes focused and verify the numerical meaning as well as code execution.
Use a new output directory for every demonstration. The public package is a
reduced research companion; do not add measured data or experimental operating
rules as fixtures.

Before proposing a change, run the tests, Ruff checks, wheel build and synthetic
demo described in the README. Include a short explanation of behavior and the
validation performed. A new mathematical assumption needs a corresponding test
with known truth or an independent reference calculation.

For a reviewed edit to existing approved files:

```bash
python tools/update_manifest.py
git add --pathspec-from-file=PUBLIC_FILES.txt
python tools/check_release.py
```

`PUBLIC_FILES.txt` mirrors the JSON allowlist for explicit staging. Adding a new
path requires reviewing its full content, updating both lists, then regenerating
the manifest. Never stage a parent research directory or copy private history.
The manifest helper only hashes already listed paths; it does not discover or
approve files. For gallery changes, generate into a new output directory and
review the images before replacing approved assets.

Do not report experimental findings in public issue attachments or CI logs.
Source availability does not grant a general reuse license; see RIGHTS.md.
