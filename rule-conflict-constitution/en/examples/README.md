This is a translation; the Chinese text is authoritative. This short page is an English guide to [examples/README.md](../../examples/README.md); the full page, with the actual output of each command, is only in Chinese.

# Example: a help center's conflict register

A small team is writing the help center for its own to-do app. The content team, the support team and the product team each have a guideline. The principal is the head of the help center, who has made these three guidelines, together with the design team's UI copy guideline, the project's rules. The help center already has several articles and a set of UI strings that the principal has accepted. Several guidelines conflict with each other, and the guidelines and the accepted deliverables also fail to match in places, so a conflict register was set up. The team, the principal, the product, the guidelines and the deliverables were all made up for this example.

The example's files are in [examples/help-center/](../../examples/help-center/), and they are in Chinese, as is the script's output. Several items turn on how to address the reader: Chinese has an informal "you", 你, and a formal one, 您.

## The six items in the register

| Item | kind | Status | What it is about |
| --- | --- | --- | --- |
| HC-01 | conflict | open | The writing guide says refund articles use 你; the support reply guide says they use 您. Both are musts, not recommendations (in the register, `strength` is `must` on both sides, and the decision sheet marks them "（必须）" ("(must)")), so the five steps apply. The two were issued on the same day with the same scope, and neither is a new version of the other, so it cannot be decided and goes to the principal. What to do until it is decided is written down. |
| HC-02 | mismatch | decided (AI, step 2) | The writing guide says account questions "have all been changed to use 你", but line 7 of the accepted FAQ still has 您. This is a description that does not match the deliverables, so it is not used as fact. |
| HC-03 | collision | decided (principal) | The glossary makes 标签 ("tag") refer only to the colored markers on tasks, but in the accepted deliverables 标签页 ("tab") refers to tabs in the interface. The principal decided that 标签页 stays as it is. |
| HC-04 | stale | decided (AI, step 1) | Version 2 of the writing guide says at the start that everything is in effect, while section 4 is still marked "pending". After comparing it word for word with version 1, it is read by the sentence newly changed in version 2. |
| HC-05 | exception | decided (principal) | The terms of service excerpt uses 您 as in the legal team's original text; registered once, and not reported again. |
| HC-06 | conflict | closed | Version 1 said button names are bold, and the design team said they are put in 「」; version 2 has already changed to 「」, so this item no longer holds. |

"Step 1" and "step 2" are steps of the resolution order (`rule_applied` in the register). The AI can only decide by steps 1 to 4; step 5 (still cannot be decided) can only go to the principal.

## How to run it

You need Python 3.9 or newer; the script uses only the standard library. Run these commands in `examples/help-center/`:

```text
python3 -I -B ../../scripts/conflict_register.py check conflict-register.json --texts-root .
python3 -I -B ../../scripts/conflict_register.py list conflict-register.json --status open --markdown
python3 -I -B ../../scripts/conflict_register.py collide --register conflict-register.json --texts-root . 标签 收藏
```

All three exit with code 0. The first checks the register, the second lists the item not yet decided as a decision sheet for the principal, and the third looks for 标签 ("tag") and 收藏 ("favorites") in the accepted deliverables. The Chinese page shows their output, and also two runs that fail on purpose and exit with code 1: one with the wrong `--texts-root`, and one with a wrong line number in the register of a copy of the example folder. The [English translation of When rules conflict](../docs/conflict-resolution.md) explains the fields, the output and the exit codes.

## What this example does not show

- The program did not decide HC-01 for anyone. Whether to use 你 or 您 is for the principal to decide; the program only checks whether the original wording, line numbers, statuses and required explanations written in the register are complete and match.
- The program does not judge which guideline is well written or should stay, nor whether the deliverables are right. HC-02's "description does not match the deliverables" was found and registered by a person; the program only checks that the registered original wording is really in those two places.
- External references (`external`) have no local file. The original wording citing them cannot be checked, and is only mentioned in `warnings`.
- That this example runs only shows that the register format and the program agree. It does not show that this approach will certainly make the work better.
