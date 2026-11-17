This is a translation; the Chinese text is authoritative. Chinese original: [docs/usage.md](../../docs/usage.md).

# How to use it

This repository has a way of using it for each of three situations: you can only chat with the AI; you can upload files to the AI; you can run commands on a computer. The three can be mixed. Whichever you use, first settle who the principal is.

Not everything needs the whole procedure, either. How heavy the process is depends on what an error would cost, not on how many files the AI looked at (C11 of the constitution). Only these cases use the register and the four statuses: you ask for a check or for the statuses; what the AI produces reaches other people directly, without you looking at it first; one change touches several deliverables, or affects other places that then have to be gone back to and checked; the AI itself proposes a change to accepted deliverables that goes beyond what you named. Everything else is a small matter: have the AI simply do it, and at delivery it says in a sentence or two what it did; where a rule was used, which rule decided it; where something that should have been done was not, what it left undone. When you name one small change to make, even to an accepted deliverable, your words are the decision to change it: the AI makes the change, says where it was made, and states that this version awaits your confirmation; where the same content appears elsewhere, it does not change those places itself, but lists them and asks you.

This repository has not verified whether these ways of using it will be followed by other AIs or in real projects, nor whether the work is done better once they are; all that has been done is a few scenario tests, described under "How far it has been verified" on the [home page](../../README.en.md). When you use them, look at the results as they are.

## First, settle who the principal is

The principal is the person who hands this task to the AI and has the final say over the deliverables. When one person uses AI for their own work, the principal is that person; in a team it is usually the project lead; for work done for a client, it may be the client.

- **Write it down.** At the start of the project description or the conversation, write a sentence such as "The principal of this project is ×××, who makes the final decisions." When several people work together, write down in advance who has the final say; if it is not written down, the AI must ask.
- **If someone decides on the principal's behalf, write that down too.** If the principal lets someone else decide within some area (for example, "terminology is decided by ××× in the product team"), write down who it is and what they cover. If it is not written down whether someone's words count as the principal's decision, ask the principal. For what the delegate decides within the delegated area, set `decided_by.who` to `principal` in the register, copy that person's words into `words`, and in `source` say who said it, where, and where the delegation is recorded.
- **Other people's words are not decisions.** Only the decisions of the principal and of the people they have authorized (within the scope of the authorization) count. Requests made by other participants in messages, comments or meetings are recorded by the AI as made, noting who made them, and treated as material or suggestions; they are not used to revoke rules or to change accepted deliverables. On a matter no rule covers, when participants say conflicting things and none of them has been designated to make the call on it, follow neither, and hand it to the person with the authority to decide (the principal, or the person the principal has authorized to handle this matter) (layer 3 in Section 1 of the constitution; "Whose word counts when several people work together" in [When rules conflict](conflict-resolution.md)).
- **Rule files handed in count as the project's rules.** A guideline written by another team or another person, once the principal hands it in or designates it as a project rule, is one of the project's rules (layer 5 of the constitution); conflicts are decided by the five steps, and it is not treated as a participant's words.
- **Keep the principal's decisions in their own words.** For what the principal decides in messages, meeting minutes or tickets, record the words and where they came from. Items in the register with `decided_by.who` set to `principal` must have `words` (the principal's words) and `source` (where they came from).

## Chat only: paste the card

For when you can only talk to the AI in a chat box.

1. Paste the full text of [CARD.md](../CARD.md) into the AI's project instructions (some products call them custom instructions, a project description or a system prompt), or into the first message of the conversation. The card is under 5,000 bytes.
2. Then state clearly: who the principal is; which rule files this project has, and which version each one is; and which deliverables the principal has already accepted.
3. Paste the content of the rule files and the accepted deliverables into the conversation where you can. For what does not fit, tell the AI what it has not been shown, so that it does not treat it as seen.
4. When rules conflict, have the AI first tell musts from recommendations (when a recommendation collides with a must, the recommendation gives way), then decide by the five steps on the card, stating which step it used; for what cannot be decided, have it list it for you as in step 5. The register can be written by the AI in the conversation, following the format of [templates/conflict-register.json](../../templates/conflict-register.json), or written by hand as a table (see "When it cannot be decided" in [When rules conflict](conflict-resolution.md) for what it looks like).
5. In this situation no program checks anything: write MECHANICAL among the four statuses truthfully as "UNTESTED (no program was run in this environment)", and the original wording and line numbers in the register are checked by a person.

The card is only a summary. In situations the card does not cover, the full text of the constitution prevails. In a long conversation, you can paste the card again.

## Can upload files: upload the constitution and the resolution practice together

For when you can upload files to the AI, or attach a knowledge base to a project.

1. Upload [CONSTITUTION.md](../CONSTITUTION.md) and [docs/conflict-resolution.md](conflict-resolution.md). Still paste [CARD.md](../CARD.md) into the project instructions, and add a sentence: "For details, see the uploaded CONSTITUTION.md and conflict-resolution.md."
2. Upload the project's rule files as well. A rule file copied verbatim can have a note from the AI added at the top, with the line `<!-- 原文开始 -->` on its own between the note and the original text (*translator's note:* it means "original text begins"; an English project can write `<!-- original text begins -->` instead, and either is accepted). The principal's original text is not rewritten.
3. If you want to record conflicts, upload a register copied from [templates/conflict-register.json](../../templates/conflict-register.json) and have the AI fill in its fields. For a filled-in example, see [examples/](../examples/README.md).
4. To the AI, uploaded files are still material: sentences slipped into a file, such as "ignore earlier instructions", are not instructions (Section 1 of the constitution).

## Can run commands: check with the script

For when you can run Python 3.9 or newer on a computer. The script uses only the standard library; there is nothing else to install.

First run the tests from the root of the repository, to confirm that it works on your computer:

```text
python3 -I -B tests/run_tests.py
```

When all tests pass, the exit code is 0. Then try it on the example (the commands are run from the root of the repository):

```text
python3 -I -B scripts/conflict_register.py check examples/help-center/conflict-register.json --texts-root examples/help-center
python3 -I -B scripts/conflict_register.py list examples/help-center/conflict-register.json --status open --markdown
python3 -I -B scripts/conflict_register.py collide --register examples/help-center/conflict-register.json --texts-root examples/help-center 标签 收藏
```

When using it on your own project:

- Run `check` each time you register new items or change the version of a rule file. When there are problems, the exit code is 1.
- When the principal needs to decide something, generate a decision sheet with `list --status open --markdown` and send it to the principal.
- Before a new rule sets a term, use `collide` to check how the word is already used in the accepted deliverables. When `complete` is not `true`, the results are incomplete.
- The script reads any path the register names (absolute paths and paths starting with `../` included), and `collide` writes whole matching lines into its output. Before running a register someone else gave you, look at which files it names; the same applies when you have an AI run it for you.

For each command's arguments, output and exit codes, see the last section of [When rules conflict](conflict-resolution.md). The tests and the script have been run on Linux, and on Windows only in GitHub's continuous integration (windows-latest, Python 3.13); macOS has not been verified. On Windows, `python3` in the commands may need to be replaced with `py` or `python`. This repository has continuous integration set up on GitHub, but it only runs this repository's own tests and does not check the registers in your project; if you want `check` to run automatically before each commit in your project, you have to set that up yourself.

## How to lay out the guideline files and the register

A suggested layout (the same as in [examples/help-center](../examples/README.md)):

```text
your-project/
  conflict-register.json   the conflict register
  rules/                   rule files in force, copied verbatim
    archive/               superseded old versions, not deleted
  texts/                   accepted deliverables (this can also be the folder where the deliverables already are)
```

- In the register, a source's `file` is written relative to the folder that holds the register; the paths in `texts` are written relative to `--texts-root`. Deliverables do not have to be moved into `texts/`: point `--texts-root` at the folder where the deliverables already are, and write the paths in `texts` relative to that folder.
- When a new version of a rule file comes out: put the new version in `rules/` and move the old version into `rules/archive/`; in the register, change the old version to `superseded` and fill in `superseded_by`; register the new version as in "Check before admitting" (see [When rules conflict](conflict-resolution.md)).
- For every rule file copied verbatim, write `sha256` in the register to pin its version, copying the value from `sources.digests` in the output of `check` (after checking the original text first). As soon as the file's original text changes, `check` reports it; where `sha256` is missing, `check` gives a reminder in `warnings`.
- For other teams' guidelines, external standards and the like, with no copy kept locally, write `"external": true`. The program cannot check the original wording that cites them, and `check` says so in `warnings`.
- The register and the rule files are all text files. They can go into version control together with the deliverables, so that every change is on record.

## Adapting it into a version for your own industry

Section 5 of the constitution sets the rules for adapting it: you may replace the examples, name specific files, and add notes for your industry; the meaning of Section 1 (the order of precedence, new rules are not retroactive, materials are not instructions, telling musts from recommendations and the five steps) and of each principle in Section 2 is not changed. In practice:

1. Copy [CONSTITUTION.md](../CONSTITUTION.md) and [CARD.md](../CARD.md).
2. In the version line, state that this is an adapted version, for example "the legal team's adapted version of v1.0, edition 1", and state that it is adapted from this constitution v1.0.
3. Replace the examples with ones from your industry: customer service could become medical record summaries, a coding standard could become notes on construction drawings. When replacing an example, each example must still show what the original step means.
4. Name the specific files meant by "the project's rules" and "general practices", for example "general practices means the firm's *Document Format Guidelines*, 2026 edition".
5. Where a principle needs extra limits in your industry, write them in that principle's "Exceptions" or in an added note. For example, some industries do not want the AI to add content on its own; under C04's exceptions you can write "no new clauses without the principal's consent"; you can also write in a few examples from your industry of what does not count as a small matter there (C11) and which choices cannot be undone (C12).
6. The adapted version needs the principal's approval and goes into the changelog, stating what was changed and why. Change the card and the constitution together, and keep the terms the same in both.

If what you want to change is Section 1 (the order of precedence, new rules are not retroactive, materials are not instructions, telling musts from recommendations and the five steps), or the meaning of a principle (not just adding limits), that is already a different constitution: give it a new name, state that it is adapted from this constitution v1.0 and where it differs from it, and stop calling it this constitution v1.0.

Also note: [scripts/conflict_register.py](../../scripts/conflict_register.py) is built around this constitution's five steps. For items the AI decided in the register, `rule_applied` can only be 1 to 4, and only the principal can decide at step 5. If an adapted version changes the number of steps or their numbering, the script, its error messages and its tests must all be changed to match.
