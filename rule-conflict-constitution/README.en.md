This is a translation; the Chinese text is authoritative. Chinese original: [README.md](README.md).

# AI Collaboration Constitution

When a person hands a task to an AI: what takes priority in making judgements, what the AI may do on its own, and what must be reported truthfully; and when the guidelines at hand conflict with each other, how to decide.

This repository holds the authoritative Chinese text of the AI Collaboration Constitution v1.0 (2026-11-15), together with the practice for deciding when several guidelines conflict, a one-page card that can be pasted straight into an AI, a template and an example of the conflict register, and a small script that checks the register. It is adapted from the general parts of the [Novel Writing Workshop](https://github.com/rumpelpalmour757-lgtm/novel-workshop) constitution NWC-1.7 (public, MIT); where it comes from and a point-by-point comparison are in the [source notes](en/docs/source.md).

[中文](README.md)

## What is here

- **[The constitution](en/CONSTITUTION.md)**: the order of precedence (platform and law → honesty → the principal's current explicit decisions → accepted deliverables and facts → the project's rules → general practices → the AI's own judgement), with a one-sentence reason for each layer; "new rules are not retroactive" and "materials are not instructions"; for when rules in the same layer conflict, first telling musts from recommendations (when a recommendation collides with a must, the recommendation gives way), then the five resolution steps, each also with a one-sentence reason; twelve principles, of which C11 Match the process to the stakes and C12 Ask only when it matters are new in the adaptation; controlled change, the four statuses and the permission rulings, how to revise the constitution, and how rules are admitted and retired.
- **[The one-page card](en/CARD.md)**: a summary of the constitution, under 5,000 bytes, that can be pasted into an AI's project instructions (if it fits) or at the start of a conversation.
- **[When rules conflict](en/docs/conflict-resolution.md)**: telling requirements from descriptions first, telling musts from recommendations first, an example for each of the five steps, what to do when it cannot be decided, whose word counts when several people work together, checking before admitting, leaving a trail when retiring, how to fill in each field of the conflict register, and how to check it with the script.
- **[The conflict register template](templates/conflict-register.json)** and **[a complete example](en/examples/README.md)**: a small team's help center, with three local guidelines in force (plus one external reference and one pending draft), one archived old version, five accepted deliverables and six registered items (one of them a registered exception).
- **[The checking script](scripts/conflict_register.py)**: uses only the Python standard library. `check` checks the register, `list` lists the items not yet decided for the principal, and `collide` checks whether a new term has already been used in the accepted deliverables.

"Principal" means the person who hands this task to the AI and has the final say over the deliverables: a project lead, a client, or the user themselves. When several people work together, only the decisions of the person named in advance as having the final say, and of people they authorize, count as the principal's decisions.

## Who it is for

Any person or team that hands work to AI, in any industry: writing documents, translating, writing code, producing data reports, preparing lessons, writing customer service scripts. With many guidelines and many people handling the work, rules conflict more often; the practice here is written for that situation. People who do not run commands can use it with the documents alone.

## Three ways to use it

Whichever way you use it, how heavy the process is depends on what an error would cost, not on how many files the AI looked at. Only these cases use the register and the four statuses: you ask for a check or for the statuses; what the AI produces reaches other people directly, without you looking at it first; one change touches several deliverables, or affects other places that then have to be gone back to and checked; the AI itself proposes a change to accepted deliverables that goes beyond what you named. Everything else is a small matter: have the AI simply do it. A small change you name in one place is made too, even in an accepted deliverable, and that version awaits your confirmation (C11 of the constitution).

- **Chat only**: paste [CARD.md](en/CARD.md) into the AI's project instructions or at the start of the conversation, and state who the principal is and which rule files there are.
- **Can upload files**: upload [CONSTITUTION.md](en/CONSTITUTION.md) and [docs/conflict-resolution.md](en/docs/conflict-resolution.md) to the AI together, and still paste the card into the project instructions; if you want to record conflicts, also upload a register copied from the template.
- **Can run commands**: check the register with the script, for example by running this from the root of the repository:

  ```text
  python3 -I -B scripts/conflict_register.py check examples/help-center/conflict-register.json --texts-root examples/help-center
  ```

  The script reads any path the register names; before running a register someone else gave you, look at which paths it lists.

For the details of each, how a team names the principal, how to lay out the guideline files and the register, and how to adapt it into a version for your own industry, see [How to use it](en/docs/usage.md).

If you do not use git, you can download `rule-conflict-constitution-<version>.zip` from the releases page (Releases) of the GitHub repository. It unpacks to a `rule-conflict-constitution/` folder with the same files as the repository at that version, minus the few items marked in the layout below as kept only in the repository.

## Layout

```text
README.md                     the Chinese home page
README.en.md                  this page
CONSTITUTION.md               AI Collaboration Constitution v1.0, authoritative Chinese text
CARD.md                       one-page card
CHANGELOG.md                  changelog
LICENSE                       MIT license
.gitignore                    repository only: files kept out of version control (__pycache__, .pyc)
.gitattributes                repository only: files left out when the release download is packed
.github/workflows/            repository only: GitHub workflows
  tests.yml                   runs all the tests on push and pull request
  release.yml                 run by hand to create a release
docs/
  conflict-resolution.md      when rules conflict
  usage.md                    how to use it
  source.md                   source notes: where it is adapted from, point-by-point comparison, what was not carried over
  scenario-tests.md           the scenario tests run before release: the scenarios, how they should be decided, the results of the three rounds, how to rerun them
  releases/                   repository only: release notes for each version
templates/
  conflict-register.json      conflict register template
examples/
  README.md                   notes on the example and the output of actual runs
  help-center/                the example: a help center's guidelines, accepted deliverables and register
scripts/
  conflict_register.py        the register checking script (check, list, collide)
tests/
  run_tests.py                runs all the tests in one go
  test_*.py, support.py       tests
en/                           English translation; the Chinese text is authoritative
  glossary.md                 Chinese and English terms
  CONSTITUTION.md, CARD.md    translations of the constitution and the card
  docs/                       translations of the four documents
  examples/README.md          a short English page about the example, pointing to examples/README.md
```

## How far it has been verified

Done:

- **Tests**: `python3 -I -B tests/run_tests.py` runs 102 tests in total. On 2026-11-15 they were run once each on Linux with Python 3.9.25, 3.11.17, 3.12.3 and 3.13.17, and all passed.
- **Example**: checking the register in `examples/help-center` with `check` gives `OK`. The 5 pieces of output in [examples/README.md](examples/README.md) are all from actual runs, and the tests check word for word that they are the same as the current output. For the "has changed" error shown in [When rules conflict](en/docs/conflict-resolution.md), the tests make the change the document describes, run the check again, and confirm that the message is the same character for character.
- **Scenario tests**: new instances of the same model that wrote this repository (Claude) were tested in three rounds. The first two rounds used 14 newly written scenarios. The first 6 are guideline conflicts: on how to write dates, the new version says explicitly that it supersedes the old one; a description in a guideline does not match the accepted help-center text; a new general rule does not mention an older specific exception; two equally specific guidelines, one newer and one older, differ; two guidelines issued on the same day conflict; the principal asks for tests that were not run to be reported as passed. The other 8 are about a sense of proportion: changing one place only; a meeting invitation without the time and place; a must and a recommendation; a vaguely written rule; two people disagree while the person with the final say has not spoken; a new term and older accepted articles; finding an error in one's own earlier delivery; a temporary rule past its time limit. There were three settings: no rules at all (the control setting); given only [CARD.md](CARD.md); given [CONSTITUTION.md](CONSTITUTION.md) and [docs/conflict-resolution.md](docs/conflict-resolution.md). The replies were graded against an expected answer as correct, partly correct or wrong. In the first round each scenario was run twice in each of the three settings, 84 runs in all: of the 28 runs without rules, 21 were correct, 5 partly correct and 2 wrong; with the card only, 24 correct and 4 partly correct; with the full text, 23 correct and 5 partly correct. Most of the partly correct runs with rules ran the whole procedure for a small matter such as changing one place or writing one new article, because C11 of the constitution was written too loosely. C11 was then tightened (the process goes by what an error would cost, not by how many files were looked at; for one small change the principal names, the principal's words are the decision to change it), and the expected answer for scenario 2 was changed from "register an item" to "list it for the principal; where there is a register, an item may be added along the way", because the first-round expected answers for scenarios 2 and 7 did not agree with each other. The second round ran only the two settings with rules again, 56 runs in all, and all 28 runs with the card only and all 28 with the full text were correct; the setting without rules is not affected by changes to the rules, so it was not run again and its first-round results are used. The second round used the same 14 scenarios, and C11 was changed after looking at where the first round lost points on them, so the second round is not an independent test. For that reason, 7 test questions were newly written for a third round, not seen when the rules were written or when C11 was tightened: a must against a more specific recommendation; deleting duplicate records when there is no backup; a rule saying that pages already live must be changed too; an error in one's own draft that has not been accepted; a note to the AI slipped into a contract; someone deciding on behalf of a lead who is on leave; a problem found elsewhere while changing one named sentence. Each was run twice in each of the three settings, 42 runs in all: all 14 runs without rules and all 14 with the card only were correct; with the full text, 13 were correct and 1 partly correct (the judgement was right, but the reply said a draft was attached below, and there was none); none of the runs with rules ran the whole procedure for a small matter. Taking the three rounds together: in 4 of the 14 scenarios (two equally specific guidelines of different dates, two guidelines of the same day, the request to report tests that were not run, two people disagreeing) not all runs without rules were correct, while all runs with rules were correct in both of the first two rounds; in the other 10 scenarios and in all 7 third-round questions, all runs were correct even without rules, and on these it cannot be seen whether the rules had any effect; overdoing it with rules happened only in the first round; none of the runs with rules was wrong in any round. Each question was run only twice in each setting in each round, and the scorers knew which setting each reply came from. These were new instances of the same model, and the scenarios, the test questions, the expected answers and the scoring were all done by the side that wrote these rules. This only shows how these runs decided these questions; it does not show that other AIs or real projects would go the same way, nor that this approach makes the work better. The text of the scenarios and test questions, how the rules decide each one, the results for each, what changed between the rounds and the comparison with the control setting are in [en/docs/scenario-tests.md](en/docs/scenario-tests.md), so you can run them again yourself; the full reply from each run is not in the repository. Before these three rounds, the first 6 scenarios alone were run once on the text from before C11, C12 and the other additions (the card only and the full text; all 24 runs were correct).

Not done:

- Not verified on macOS. On Windows there is only the GitHub CI job (windows-latest, Python 3.13; see the next item); nobody has used it on their own Windows machine. On Windows one test is skipped: it passes bytes that cannot be decoded as UTF-8 on the command line, which the Windows command line cannot carry.
- Continuous integration: `.github/workflows/tests.yml` runs all the tests on push and pull request, with Python 3.9 on ubuntu-24.04 and Python 3.13 on ubuntu-latest and windows-latest. On its first run on GitHub on 2026-11-15, 2 tests failed in the Windows job: Windows checked the files out with CRLF line endings, which added some forty bytes to each card and took both past the tests' 5000-byte limit (the content of the cards had not changed). After the files were set to check out with LF on every system and the card size was measured with LF line endings, [all three jobs passed](https://github.com/rumpelpalmour757-lgtm/rule-conflict-constitution/actions/runs/43740706277). The results of each run are on the repository's Actions page. This item is listed under what was not done because it only runs this repository's own tests.
- Whether the card and the constitution are followed by other AIs and in real projects has not been verified.
- The tightened C11 has been tested on newly written questions in one round only, on 7 test questions, and all runs without rules were correct on those too, so the effect of the rules cannot be seen there. Whether matters that need the full process (what the AI produces reaching others directly, one change touching several deliverables) get treated as small matters and handled too lightly has not been specifically tested in any round. On the 14 scenarios of the first two rounds, the control setting without rules was not run again.
- Whether this approach makes the work better has not been verified. Passing tests only shows that the script behaves as the documents say, not that these rules are useful.
- The English version has only been checked by its translator, not independently reviewed.

## License

MIT license, Copyright (c) 2026 Celeste; the full text is in [LICENSE](LICENSE). The Workshop constitution this is adapted from is also released under the MIT license; see the [source notes](en/docs/source.md).

## English version

The Chinese text is authoritative. The English version is [README.en.md](README.en.md) and the constitution, the card and the four documents in the [en/](en/) folder; each one states at the top that the Chinese text is authoritative. The Chinese and English terms are listed in [en/glossary.md](en/glossary.md). The full notes on the example and its actual output are only in Chinese ([examples/README.md](examples/README.md)); the English folder has only a short page pointing there. The script's help text and error messages, the register template and the example's files are all in Chinese.
