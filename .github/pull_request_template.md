<!-- Generated from .github/pr-rules.toml. Do not edit by hand;
     edit the config and run .github/scripts/generate_pr_template.py -->

## What changed

<!-- One or two lines. What does this PR do? -->


## Why

<!-- Reason for the change. Link the issue: Closes #123 -->

<!-- Required: Link an issue, e.g. "Closes #12" -->


## Data impact

<!-- Delete this section if no CSV files changed. -->

- Files touched:
- Rows added / removed / modified:
- Column schema changed? (yes / no — if yes, list columns)
- Backward compatible with existing parsers?


## Build evidence

<!-- Paste a screenshot of the build finishing successfully. Drag the image into
this box, or copy-paste it — GitHub uploads it and inserts the markdown.
Windows, macOS or Linux is fine. The whole terminal output must be readable,
including the final summary line and the total time.
 -->


## How to verify

<!-- Exact steps a reviewer can follow. -->

1.
2.


## Notes for reviewer

<!-- Anything risky, anything you are unsure about, anything to look at first. -->


## Checklist

- [ ] The build screenshot above is from this branch and shows the build finishing with no errors
- [ ] Column count is unchanged, or the change is described above
- [ ] No unescaped commas or line breaks inside fields
- [ ] File still parses (`python3 -c "import csv; list(csv.reader(open('inditeProducts1.csv')))"`)
- [ ] No credentials, personal data, or internal-only values committed
- [ ] PR title describes the change, not the file name
- [ ] Correct code owner is requested for review
