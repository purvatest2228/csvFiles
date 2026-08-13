## What changed

<!-- One or two lines. What does this PR do? -->

## Why

<!-- Reason for the change. Link the issue: Closes #123 -->

## Data impact

<!-- Delete this section if no CSV files changed. -->

- Files touched:
- Rows added / removed / modified:
- Column schema changed? (yes / no — if yes, list columns)
- Backward compatible with existing parsers?

## How to verify

<!-- Exact steps a reviewer can follow. -->

1.
2.

## Checklist

- [ ] Column count is unchanged, or the change is described above
- [ ] No unescaped commas or line breaks inside fields
- [ ] File still parses (`python3 -c "import csv,sys; list(csv.reader(open('inditeProducts1.csv')))"`)
- [ ] No credentials, personal data, or internal-only values committed
- [ ] PR title describes the change, not the file name
- [ ] Correct code owner is requested for review

## Notes for reviewer

<!-- Anything risky, anything you are unsure about, anything to look at first. -->
