This is a translation; the Chinese text is authoritative. Chinese original: [docs/conflict-resolution.md](../../docs/conflict-resolution.md).

# When rules conflict

A project's rule files keep multiplying: the writing guides, glossaries, checklists and conventions sheets the principal gives, and the conventions set within the project itself. In the [AI Collaboration Constitution](../CONSTITUTION.md) they all sit in layer 5, "the project's rules", and none of them overrides another. The general practices of a team or an industry sit in layer 6: when they conflict with the project's rules, go straight by the order of precedence, and the project's rules come first. Only when the principal designates a general document as one of the project's rules does it count as layer 5. Section 1 of the constitution, "Within the same layer", first tells musts from recommendations and then gives five resolution steps, and Section 6, "Admitting and retiring rules", requires that both entry and retirement be registered. This document describes how to do it in practice.

You can follow it without running commands: the register can be written by hand and checked by a person. If you can run commands, check the register with [scripts/conflict_register.py](../../scripts/conflict_register.py); see the last section.

The examples below were made up to illustrate these steps. They are not content from any real project.

## When to use this

- Two rules in the same layer say different things, for example two guidelines requiring different things for the same matter.
- What a rule says does not match the accepted deliverables, for example a guideline saying "everything has already been changed" while the deliverables still have parts that have not.
- A newly set term collides with an existing use in the deliverables, for example a glossary wanting a word to refer only to one thing while that word already refers to something else in the deliverables.
- The same rule file contradicts itself, for example saying at the start that everything is in effect while a later item is still marked as pending.
- On a matter no rule covers, participants say different things, and none of them has been designated to make the call on it, for example two colleagues, one wanting the full name and the other the short name (see "Whose word counts when several people work together" below).

Between different layers, do not use this; go straight by the order in Section 1 of the constitution. Platform and legal requirements, honesty, the principal's current explicit decisions, and accepted deliverables and facts all sit above the project's rules; the project's rules in turn sit above general practices.

Two more cases do not need the whole procedure either. When one rule is a recommendation and the other a must, the recommendation gives way; that is not a conflict (see "First, tell musts from recommendations"). The other case is small matters (C11 of the constitution). How heavy the process is depends on what an error would cost, not on how many files were looked at: conflicts are registered and the four statuses recorded only when the principal asks for a check or for the statuses, when what the AI produces reaches other people directly without the principal looking at it first, when one change touches several deliverables or affects other places that then have to be gone back to and checked, or when the AI itself proposes a change to accepted deliverables beyond what the principal named. Everything else is a small matter and is simply done, such as fixing a typo in a draft not yet accepted or changing one date as the principal said; a single place the principal names is changed even in an accepted deliverable: say where the change was made, and state that this version awaits the principal's confirmation; where the same content appears elsewhere, do not change those places yourself, but list them and ask the principal (the simplified path in Section 3 of the constitution). When a small matter runs into a rule conflict: if steps 1 to 4 decide it, say in a sentence in the reply which step decided it; if a rule file itself is wrong (for example, a description does not match the deliverables), list it for the principal and ask them to correct it; if it cannot be decided, still apply neither rule, say so clearly in the reply and hand it to the principal. In the last two cases, if the project already has a conflict register, an item may be added to it along the way (one that cannot be decided is recorded as pending the principal's decision); if it has none, there is no need to set one up for this.

Practices the principal has explicitly marked as intentional (quotations copied verbatim, clauses that must be reproduced exactly as in the original) are not conflicts. Register them once (with `kind` set to `exception`), and do not report the same place again.

*Translator's note:* some examples below are about how to address the reader. Chinese has an informal "you", 你, and a formal one, 您.

## First, tell requirements from descriptions

What a rule file says comes in two kinds, which are handled differently:

- **Requirements**: what should be done from now on. "Address the user as 你", "attachments are in PDF", "function names use lowercase with underscores". Follow them. When two requirements conflict, decide by the five steps below.
- **Descriptions**: what already is, or what something else says. "All account questions have already been changed", "this section was not touched in the previous version", "the brand manual requires product names in all capitals". Verify a description against the original first: a description of the deliverables against the accepted deliverables, a paraphrase of a standard against the standard's original text. If it matches, it can be used as fact. If it does not, it is not a rule: the deliverables stay as accepted, the principal's file is not changed, and the difference is listed for the principal.

When one sentence contains both, take it apart. In "per the brand manual, product names are always in all capitals", the first half is a description (what the brand manual says) and the second half is a requirement. If the first half does not match, the requirement does not stand; that belongs to step 2. If the rule says explicitly "this is our team's own choice", it is not a paraphrase, and it belongs to step 3.

## First, tell musts from recommendations

The requirements in rules also differ in strength:

- **Must**: no room for negotiation. Rules that say "must", "always" or "must not" are musts; a requirement without words such as "recommended" or "as far as possible" is also treated as a must. "Attachments are in PDF" does not say "must", and it is still a must.
- **Recommendation**: rules with words such as "recommended", "as far as possible" or "generally". "Keep titles to 20 characters or fewer as far as possible" and "generally, put the conclusion first" are recommendations.

When a recommendation collides with a must, the recommendation gives way: follow the must; this is not a conflict and does not need registering. Example: a team's *How to Write the Weekly Report* says "keep each entry to one line as far as possible", and its *Risk Reporting Requirements* say "each risk in the weekly report must state its cause, impact and response". When a risk does not fit on one line, write it on several lines as the latter requires, and do not register a conflict.

The same holds when the recommendation is the more specific rule. Example: a team's *Email Guide* says "external emails carry the signature block", and the *Customer Service Scripts* say "replies to tickets generally leave out the signature block"; ticket replies are external emails too. The latter is more specific, but it is a recommendation and the former is a must, so ticket replies still carry the signature block. Telling musts from recommendations comes before the five steps, and step 3, "the specific beats the general", applies only between two musts. For ticket replies to go without the signature block, that rule has to be written as a must, or the principal has to say so separately.

When two rules are both only recommendations and cannot both be followed, that is not a conflict either: choose one according to the purpose of each, and at delivery say which one was chosen and why.

Neither of these is a conflict, and they are generally not registered. Where the principal or the project's rules require a record of everything (the exception in C11 of the constitution), record a `conflict` item with `status` set to `closed` and a `resolution` saying whether a recommendation gave way or both were recommendations, and which rule was followed; on a recommendation's side `strength` is `should`, on a must's side `must`. Do not write `decided_by`: telling musts from recommendations is not one of the five steps, so `rule_applied` has no value to take.

Only between two musts are the five steps below followed. When registering the rules involved in a conflict, write `strength` in `sides`: `must` (a must) or `should` (a recommendation); see "How to fill in each field of the conflict register".

A vaguely written rule is understood by its purpose, and how it was understood is recorded; it is not treated as a hard metric that can be counted. Example: the *Customer Service Scripts* say "keep replies as concise as possible". What this wants is for the customer to see the answer at a glance, so it can be understood as "put the conclusion first and delete repeated pleasantries"; it is not understood as "no more than 50 characters", and steps the customer has to follow are not deleted to save characters. Write how it was understood into the delivery note; if the principal disagrees, they can change it.

Telling musts from recommendations applies only between rules in the same layer. What the principal says in the current message is handled at layer 3 of the constitution and prevails over the project's rules; if it is worded with "as far as possible", follow it as far as it can be done, and if it is unclear whether it is a decision at all, judge by C12 of the constitution whether to ask.

## The five resolution steps

These five steps apply between two rules that are both musts, after sorting them by strength as in the previous section. Stop at the step that decides it, and state which step it was. The AI may decide by steps 1 to 4 on its own; only the principal can decide at step 5. Section 1 of the constitution gives a one-sentence reason after each step. In situations the text does not cover, you can use the reasons to judge which step a case belongs to; if the reasons still do not decide it, hand it to the principal under step 5.

### Step 1: The principal's latest explicit decision

What the principal says explicitly in the current message, or what a rule file says explicitly that it supersedes, revokes or amends: follow the latest such statement. When a new version of the same rule comes out, follow the new version. Merely writing a new, different rule that does not name the old one is not a revocation. Statements describing deliverables are not decisions; they belong to step 2.

Example: version 1 of a team's *Meeting Minutes Format*, item 2, says "write dates as 1 March 2026". Version 2 says explicitly "Item 2 of this version supersedes item 2 of version 1: write dates as 2026-03-01". Follow version 2 (step 1).

- Later a *Meeting Minutes Supplement* comes out, which only adds "list the action items and their owners at the end of the minutes" and says nothing about dates. Dates still follow version 2; the supplement revokes nothing.
- The principal says in a message "for these minutes going to the client, write the date as 1 March". These minutes follow what the principal said; record the words and where they were said. If the principal has not made clear whether later minutes should do the same, write later ones as version 2 says for now, and list the question at delivery for the principal to confirm (C12 of the constitution).

When the same file says at the start that something is done while a later item is still marked as to-do, read it by the sentence newly changed in this version, and record an item so that the principal knows. Which sentence is new can be found by comparing word for word with the previous version, so keep the old version. HC-04 in the [example](../examples/README.md) is this case.

### Step 2: A verified requirement beats an unverified description

First separate requirements from descriptions as in the previous section. A description that does not match the original is not a rule: the deliverables stay as accepted, and the difference is listed for the principal. When a rule paraphrases a standard, that is also a description; if it does not match the standard's original text, the standard's original text prevails.

Example: a *Course Handout Style Guide* says "lectures 1 to 6 all have after-class exercises attached". Checking the accepted handouts, lecture 4 has no exercises. This sentence is a description, and it does not match the deliverables. Do not use it as fact (for example, do not write "every lecture has exercises" in the course introduction). The accepted lecture 4 stays as it is, the style guide is not changed either, and the difference is listed for the principal; whether to add exercises to lecture 4 is for the principal to decide. In the register, record a `mismatch` item, decided by the AI at step 2.

Example: the support team's *Reply Scripts Guide* says "per the brand manual, product names are always in all capitals". The brand manual's original text says "product names start with a capital letter". A rule that claims "this is what the standard requires" and does not match the original belongs to this step: the brand manual's original text prevails, and the difference is listed for the principal.

### Step 3: The specific beats the general

A rule aimed at one place, one object or one kind of content (such as refund articles, or the parameter tables in an appendix) beats a rule aimed at the whole project; the project's conventions beat general standards of right and wrong (here meaning general standards the principal has listed as the project's rules). In the examples below, both sides are the project's rules (layer 5). A team's general document that the principal has not designated sits in layer 6 and cannot override the project's rules in the first place, so this step is not needed for it.

Example: the principal lists the team's general *Coding Standard* as one of the project's rules; it requires "function names use lowercase with underscores". The project's own *Payment Module Integration Notes* say "function names in this module follow the other side's API documentation". The payment module follows the integration notes, and the other modules follow the *Coding Standard* (step 3).

Where the principal says explicitly that something is this project's choice and stricter than the general standard, follow it, but do not judge wording that the general standard allows as wrong. Example: the same *Coding Standard* says "no more than 120 characters per line"; in the project's notes the principal adds "no more than 80 characters per line in this project; this is the project's choice". New code follows 80. When pointing out a line of 100 characters in old code, say it is "longer than the 80 set for this project", not that it is "wrong".

If a newly set general rule does not explicitly revoke an older specific exception, the exception stays in effect. Example: version 1 of a translation style guide says "keep the API parameter tables in the appendix in the original English". Version 2 adds a general rule, "translate the whole manual into Chinese", without mentioning the appendix. Version 1 is marked as superseded in the register, but version 2 neither rewrites the appendix item nor deletes it by name, so the parameter tables in the appendix still stay in English (step 3); when registering this exception, state that it is cited from version 1. A general rule the principal states in a message that does not mention the appendix does not revoke this exception either; if it is unclear whether the principal means to include the appendix, keep the appendix in English for now and list the question at delivery for the principal to confirm (C12 of the constitution).

If the principal has set a separate limit on accepted parts (for example, "for the few articles already published, further changes are limited to necessary minor adjustments"), follow the limit. Items in a general checklist that say "must be changed whenever found" fall into two kinds for these articles: those that are only a matter of wording, which may or may not be changed, are recorded only as optional; items of the kind the limit still requires changing (anything that would make readers mistake one thing for another or get a number wrong) are still changed.

### Step 4: Between equally specific rules, the newer date beats the older

When two rules govern the same matter with the same scope, and neither is a new version of the other, follow the one with the newer date.

Example: the principal lists both the operations team's *How to Write Event Notices* of 2 March and the marketing team's *Key Points for Event Copy* of 10 May as the project's rules. The former says "notice titles begin with the event name"; the latter says "titles of event notices begin with the date". Both govern the titles of all event notices with the same scope, neither is a new version of the other, and the two cannot both be followed. Follow the one of 10 May: titles begin with the date (step 4). In the register, record a `conflict` item with status `decided`, decided by the AI, with `rule_applied` set to 4, and also list it so that the principal knows.

### Step 5: If it still cannot be decided, apply neither rule

If none of the first four steps decides it, stop here and hand it to the principal.

Example: the marketing team's *Brand Guide* and the product team's *UI Glossary* are both project rules the principal has handed in, and both were issued on 1 September 2026. One writes "NoteBox", the other "Notebox", and both govern the product name in all public-facing text. The principal has never said (step 1 cannot decide it); both are requirements (step 2 cannot decide it); the scope is the same (step 3 cannot decide it); they are from the same day (step 4 cannot decide it). That leaves step 5: apply neither, and proceed as in the next section.

## When it cannot be decided

1. **Apply neither rule.** Do not change accepted deliverables to follow either rule, and do not quietly pick a side for new work.
2. **Register it.** Record it in the conflict register with `status` set to `open`, stating what the principal needs to decide (`ask`) and what to do until it is decided (`meanwhile`). You may also write since when it has been pending (`since`) and the AI's proposal (`proposal`).
3. **What to do until it is decided.** Accepted deliverables stay as they are and are not changed to follow either rule. New work avoids the disputed practice where it can (using different wording, or holding off on a name); where it cannot, mark the spot for the principal to decide. In the product-name example above, new text that can say "this app" says "this app"; places that must give the product name, such as the app store title, are left blank for now and marked "product name pending the principal's decision".
4. **Give the principal a decision sheet.** Set out side by side the original wording of both sides, where each is, the AI's proposal and what is done until it is decided, so that the principal can see at a glance what needs deciding. If you can run commands, generate it from the register with `list --markdown` (see the last section); if you cannot, write it by hand in the form shown below.
5. **After the principal decides.** Record the principal's words and where they came from (which message, which minutes), change the status to `decided`, and set `decided_by.who` to `principal`. A decision made by someone the principal has authorized, within the scope of the authorization, is recorded the same way, with `source` stating who said it and where the authorization is written (see "Whose word counts when several people work together" below). The principal's rule files are changed by the principal or by the file's owner; the AI does not change them on their behalf. Any new version that results is registered as in "Check before admitting".

A pending item that states clearly what to do until it is decided does not hold up other work.

HC-01 in the [example](../examples/README.md) is a pending item. The decision sheet that `list --markdown` generates for it is:

```markdown
## 帮助中心改版（示例）：还没定的条目（共 1 条）

- **HC-01**（规则打架，还没定，自 2026-11-05 起）写作规范和客服回复规范对退款类文章的称呼说法不同：退款类文章称呼用户用“你”还是“您”？
  - 定下之前：已采纳的退款说明照原样，不按任何一条改；新写的退款类文字尽量不直接称呼用户（比如写成“申请提交后，款项会在 7 个工作日内原路退回”），避不开的地方标出来交委托人定。
  - 写作规范第二版，第一节第 2 条（必须）：退款类文章也用“你”
  - 客服回复规范，第二节第 1 条（必须）：退款类文章称呼用户用“您”
  - refund（texts/refund.md）第 3 行：您的退款申请提交后
  - AI 的建议：两条都是必须，不是建议；两份规范同一天发，管的都是退款类文章，谁也不是谁的新版本，按裁决顺序定不了。请委托人选一个；选定后，由内容组或客服组把自己那一份改成一致的说法。
```

*Translator's note:* the script prints the sheet in Chinese, as above. In English it reads:

```markdown
## Help center revamp (example): items not yet decided (1 in total)

- **HC-01** (rule conflict, not yet decided, since 2026-11-05) The writing guide and the support reply guide say different things about how refund articles address the user: should refund articles address the user as 你 or 您?
  - Until it is decided: the accepted refund article stays as it is and is not changed to follow either rule; new refund text avoids addressing the user directly where possible (for example, "once the request is submitted, the money is returned to the original payment method within 7 working days"), and places where this cannot be avoided are marked for the principal to decide.
  - Writing guide v2, section 1, item 2 (must): refund articles also use 你
  - Support reply guide, section 2, item 1 (must): refund articles address the user as 您
  - refund (texts/refund.md), line 3: after your (您) refund request is submitted
  - AI's proposal: both are musts, not recommendations; the two guidelines were issued on the same day, both cover refund articles, and neither is a new version of the other, so the resolution order cannot decide it. The principal is asked to choose one; once it is chosen, the content team or the support team changes its own guideline to say the same.
```

When writing it by hand, you can use a table:

| Item | For you to decide | One side | The other side | Original wording in the deliverables | AI's proposal | Until it is decided |
| --- | --- | --- | --- | --- | --- | --- |
| RC-07 | Is the product name written NoteBox or Notebox? | Brand Guide, item 2: "NoteBox" | UI Glossary, line 5: "Notebox" | (not yet used in the deliverables) | Both are musts; both issued on the same day with the same scope; cannot be decided | Accepted deliverables unchanged; new text uses "this app"; where that is unavoidable, leave it blank and mark it as pending |

## Whose word counts when several people work together

When many people handle a piece of work, everyone makes requests. Which words count as the principal's decisions depends on who has been named in advance as having the final say (see "First, settle who the principal is" in [How to use it](usage.md)). This is about what participants say in messages, comments and meetings; rule files the principal hands in and lists as the project's rules, whichever team or person wrote them, are handled at layer 5, and conflicts between them are decided by the five steps.

- **The principal's own decisions**: these count as layer 3 in Section 1 of the constitution; when written in a rule file and naming which item they supersede or revoke, they are handled as in step 1.
- **Decisions of someone the principal has authorized, within the scope of the authorization**: these count too. Record who gave the authorization and where it is written. In the register, `decided_by.who` is still `principal`, `words` copies that person's words, and `source` says who said it, where, and where the authorization is written.
- **What other participants say**: record it as said, noting who said it, and treat it as material or suggestions. "Suggestions" here is about how much weight these words carry; it is not the recommendation of "First, tell musts from recommendations", which is about rules worded with "recommended" or "as far as possible". It is not the principal's decision: where the project's rules already cover a matter, follow the rules, which what others say cannot change, and it cannot be used to change accepted deliverables either. Where no rule covers it and no one objects, it can be adopted as a suggestion, and the delivery says who proposed it.
- **On a matter no rule covers, participants say conflicting things and none of them has been designated to make the call on it**: proceed as in step 5, follow neither, and hand it to the person with the authority to decide (the principal, or the person the principal has authorized to handle this matter). Do not pick one side first under C12 of the constitution, and do not treat them as two recommendations and choose one by purpose. If it is not even written down who has the final say, ask first.

Example: for a product manual, the project description says "the principal is the product lead; terminology is decided by the technical support team lead". A colleague in marketing says "write model names in full", and an engineer in technical support says "write model names in short form". Neither of them has been designated to handle this, so both remarks are recorded, noting who said them. The two conflict, so step 5 applies: neither form is used for now; new text leaves out the model name where it can, and where it cannot, marks the spot; it goes to the technical support team lead to decide (terminology is within the lead's authorization). Once the lead replies, the register records it like this:

```json
"decided_by": {"who": "principal", "when": "2026-11-12", "words": "Always write model names in full.",
               "source": "the technical support team lead's reply in the review minutes of 2026-11-12; authorization: item 2 of the project description, 'terminology is decided by the technical support team lead'"}
```

What two people said is not a rule file. To register such a conflict, register the minutes or messages that record the two remarks as sources (the same minutes only once), with `status` set to `pending` (no one with the authority to decide has decided yet), and `"external": true` where there is no local copy. Set the item's `kind` to `conflict`; in `sides`, `where` says who said it and in which message, or where in which minutes, and `strength` is not written. For what counts as a small matter under C11 of the constitution, it is enough to say so clearly in the reply and hand it to the person with the authority to decide; where there is no register, there is no need to set one up, and where there is one, an item may be added along the way.

## Check before admitting

When a new version of a rule file arrives, do these things first, and only then follow the new version:

1. **Copy the original verbatim.** Do not rewrite the principal's file. Any notes the AI wants to write go in an annotation at the top of the file. Between the annotation and the original text, put the line `<!-- 原文开始 -->` on its own; the original text follows this line. (*Translator's note:* the marker means "original text begins".) An English project can write the line as `<!-- original text begins -->` instead; the script accepts either. Record the version and date, and pin the version by recording the sha256 of the original text (see `sha256` below for the algorithm). The program does not require `sha256`, but without it a change to the original text cannot be reported by `check`; it only gives a reminder in `warnings`. Keep old versions in the archive folder; do not delete them.
2. **Compare with the existing rules.** Where the same matter is stated differently in two places, first tell musts from recommendations: where a recommendation gives way, record nothing (if a record is required, record it as `closed`, as described in "First, tell musts from recommendations"); where both are musts, record a `conflict` item, with `strength` set to `must` on both sides.
3. **Compare with the accepted deliverables.** Do the descriptions in the new rule ("already changed", "this section was not touched") match the deliverables? Where they do not, record a `mismatch` item. Where a requirement in the new rule differs from the accepted deliverables (for example, a new rule sets how dates are written, while accepted older articles still use the old form), the deliverables are not wrong, and they are not changed automatically: the new rule governs what is newly done from then on; whether the accepted deliverables should change to follow it is listed for the principal to decide, and once that is decided, the controlled change in Section 3 of the constitution is followed. Where a rule states for itself which period or which kind of content it governs, follow the scope it states; where that scope includes accepted deliverables, or the rule says explicitly that accepted deliverables must change too, list them likewise for the principal, and ask the principal to name which ones to change. This is about the project's rules and general practices; when platform or legal requirements change, follow layer 1 in Section 1 of the constitution, and "not retroactive" is no reason not to change; where that means changing accepted deliverables, list them for the principal too and follow controlled change.
4. **Search the deliverables for new terms.** When a new rule wants a word to refer only to one thing, first check whether that word already refers to something else in the accepted deliverables. If it collides, record a `collision` item. If you can run commands, use `collide` (see the last section). If you cannot, search each file with your editor's search, and record which files you searched.
5. **All results go into the register** and are decided by the five steps; what cannot be decided is listed for the principal. Where checklists or conventions sheets that follow this rule need updating, the update is also recorded as an item.

## Leave a trail when retiring

- **Superseded**: change the source's `status` to `superseded`, set `superseded_by` to the source that superseded it, and write in `note` from when. The original text is not deleted, and the archived file can stay in `file`. Marking a whole file as superseded means that version is no longer the one in force; specific exceptions in the old version that the new version neither rewrites nor deletes by name do not lapse with it (step 3 of "Within the same layer" in Section 1 of the constitution), and items citing them still cite the archived old version.
- **Not yet decided by the principal**: set `status` to `pending`. It is not a valid rule, and deliverables are not changed on its basis.
- **A temporary rule with a stated time limit**: once the limit has passed, it is no longer a rule in force, and new work is not done on its basis. The register's `status` has no "expired" value, and `check` does not look at dates: for one that has expired, `status` stays `in_force` only because there is no other value to write; it does not count as in force. Write its time limit and "expired" in the source's `note`. `check` reports nothing because it has expired, so check the still-open items that cite it again yourself against the rules in force.
- **A cited rule file changes version**: the items citing it must be checked again against the new version before the register is valid. For a source with a pinned `sha256`, as soon as the file's original text changes, `check` reports it (see the last section). If an item that is still open cites only superseded sources, `check` also reports it: check it again against the version in force first.
- **A rule in two conflicts**: first ask whether it should stay and whether its scope should be narrowed, and only then ask how the deliverables should change. More rules does not mean better work.

## How to fill in each field of the conflict register

The register is a UTF-8 JSON file, with or without a BOM at the start. The template is [templates/conflict-register.json](../../templates/conflict-register.json), and a filled-in example is [examples/help-center/conflict-register.json](../../examples/help-center/conflict-register.json). Keys are in English; values can be written in Chinese. Do not write duplicate keys in the same object: JSON keeps only the last one, and `check` reports it. `note` can be written in any object, and the program does not read it; the program does not read keys missing from the tables below either, and `check` gives a reminder about them in `warnings` (most likely they are misspelled, such as `SHA256` for `sha256`). The register must be standard JSON: `check` reports `NaN`, `Infinity`, numbers that overflow (such as `1e400`) and unpaired escapes such as `\uD800` as errors.

### Top level

| Field | Required | How to fill it in |
| --- | --- | --- |
| `schema` | Yes | Always `"conflict-register/1"`. If it is wrong, `check` reports only this and checks nothing further |
| `project` | Yes | The project name, a non-empty string |
| `updated` | Yes | The date of the latest check. The program only checks that it is non-empty, not the date format |
| `note` | No | A note for people; the program does not read it |
| `sources` | Yes | The list of rule files, at least one |
| `texts` | No | The accepted deliverables: an object mapping deliverable ids to paths. Leaving it out or writing `null` counts as empty |
| `items` | Yes | The list of items; it can be an empty list |

### `sources`: one entry per rule file

| Field | Required | How to fill it in |
| --- | --- | --- |
| `id` | Yes | A non-empty string, no duplicates. Items cite this file by it |
| `title` | Yes | The name of the file |
| `version` | Yes | The version, such as "version 2" or "2026-11-01" |
| `date` | Yes | The date of this version |
| `status` | Yes | One of `in_force` (in force), `superseded` (superseded), `pending` (not yet decided by the principal). For how to write a temporary rule whose time limit has passed, see "Leave a trail when retiring" |
| `label` | No | A short name shown in the decision sheet; if left out, `title` is shown |
| `file` | Required for local files in force | The path of the rule file, relative to the folder that holds the register. For superseded or pending sources, write it if there is an archived copy. Whatever the status, once it is written it is checked: whether the file exists, whether it is UTF-8, whether `sha256` matches, whether the original wording is there |
| `sha256` | Required for local files copied verbatim | The digest of the original text: 64 hexadecimal digits, upper or lower case. The program does not enforce it: for a local file that was read without one, `check` gives a reminder in `warnings`; for external references and sources without `file`, it cannot be checked even if written, which is also noted, but its format is still checked |
| `superseded_by` | Required for `superseded` | Which source superseded it (that source's `id`). Following the chain must end at a source that is in force or pending; a loop, or pointing at itself, is an error. Sources that are not `superseded` must not have it |
| `external` | No | For an external reference (such as another team's guideline, or a standard, with no copy kept here), write JSON `true`, and `file` is then not required. Only `true` counts: `false`, `null` or leaving it out all count as a local file; a string or a number is an error, and the source is checked as a local file |
| `note` | No | A note; the program does not read it |

The `sha256` algorithm: read the file as UTF-8, remove a BOM at the start, and replace CRLF and lone CR with LF. If the file has a line that, after trimming leading and trailing whitespace, is exactly `<!-- 原文开始 -->` or its English form `<!-- original text begins -->`, only the text after that line is counted; otherwise the whole text is. If both forms appear, the first one in the file counts, and the later marker line is part of the original text. Then encode it as UTF-8 and take the SHA-256. So changing the annotation does not count as changing the original text, and a copy saved on Windows (CRLF, with a BOM) gives the same digest. For a UTF-8 file with LF line endings, no BOM and no such marker line, the result is the same as what `sha256sum` computes. The easiest way is to run `check` once and copy the value from `sources.digests` in its output, after checking the original text first.

### `texts`: the accepted deliverables

Deliverable ids map to paths. Paths are relative to the `--texts-root` folder given at run time, and must be non-empty strings. Register only versions the principal has accepted; drafts that have not been accepted are not registered.

```json
"texts": {
 "faq-account": "texts/faq-account.md",
 "ui-strings": "texts/ui-strings.json"
}
```

### `items`: one entry per item

| Field | Required | How to fill it in |
| --- | --- | --- |
| `id` | Yes | A non-empty string, no duplicates |
| `title` | Yes | One sentence saying what the matter is |
| `kind` | Yes | See the table below |
| `sides` | Yes | The evidence for both sides, as a list. At least 1 entry for `exception`, at least 2 for the others |
| `status` | Yes | One of `open` (not yet decided), `decided` (decided), `closed` (closed) |
| `ask` | Required for `open` | What the principal needs to decide, written as a question. Left on items in other statuses, it is not reported |
| `meanwhile` | Required for `open` | What to do until it is decided. Left on items in other statuses, it is not reported |
| `since` | No | Since when it has been pending; the decision sheet shows "自 … 起" ("since …") |
| `proposal` | No | The AI's proposal; shown in the decision sheet |
| `resolution` | Required for `decided` and `closed` | How it was decided, or why it was closed. Must not be written on `open` items |
| `decided_by` | Required for `decided` | Who decided it; see below. It may be written on `closed` items, and is then checked by the same rules; it must not be written on `open` items |
| `note` | No | A note; the program does not read it |

An `open` item must not cite only superseded sources: check it again against the version in force first.

| `kind` | When to use it |
| --- | --- |
| `conflict` | Two rules conflict |
| `mismatch` | A description in a rule does not match the accepted deliverables |
| `collision` | A new term collides with an existing use in the deliverables |
| `stale` | The same file contradicts itself |
| `exception` | A practice the principal has explicitly marked as intentional; registered once and not reported again |

### `sides`: one entry per side

A rule side cites one source, and a deliverable side cites one deliverable. The same entry cannot have both, and cannot have neither.

| Side | Field | How to fill it in |
| --- | --- | --- |
| Rule | `source` | The source's `id`; it must be in `sources` |
| Rule | `where` | Required: which section and item of that file |
| Rule | `quote` | Optional: the original wording, copied word for word. If written, it is looked for in the original text (where there is a marker, only after the first marker); if it is not found, that is an error |
| Rule | `strength` | Optional: whether this rule is `must` (a must) or `should` (a recommendation); see "First, tell musts from recommendations". If written, it is checked, and can only be one of these two values (writing `null` is the same as not writing it); the deliverable side must not have it. The decision sheet shows it as "（必须）" ("(must)") or "（建议）" ("(recommendation)"); a value other than these two is shown as written in JSON, in the form "（strength 写的是 "必须"，先跑 check）" ("(strength is written as "必须"; run check first)") |
| Deliverable | `text` | The deliverable's id; it must be in `texts` |
| Deliverable | `line` | Required: the line number, a positive integer counting from 1 (`true`, `3.0` and `"3"` do not count) |
| Deliverable | `quote` | Required: the original words on that line; part of the line is enough |

Original wording is compared literally, character by character: full-width and half-width forms, spaces and punctuation must all be the same. A rule's original wording that spans lines must be copied into the JSON together with the line breaks (written as `\n`). The deliverable side's original wording is only looked for within one line, so copy only words from within one line. Line numbers are counted like this: LF, CRLF and a lone CR each count as one line break; a line break at the very end does not add an extra line; form feeds, U+2028 and similar characters do not count as line breaks.

### `decided_by`: who decided it

| Field | When to write it | How to fill it in |
| --- | --- | --- |
| `who` | Required | `principal` (decided by the principal) or `ai` (decided by the AI using the resolution order). An `exception` is a practice the principal has explicitly marked as intentional, so it can only be `principal` |
| `when` | Required | The day it was decided |
| `words` | Required for `principal` | The words of the principal, or of the person they authorized |
| `source` | Required for `principal` | Where the words came from, such as "the principal's reply in the review meeting minutes of 3 November". Note that this is not the same thing as `source` in `sides` |
| `rule_applied` | Required for `ai` | Which step of the resolution order decided it: an integer from 1 to 4. Only the principal can decide at step 5, so the AI cannot write 5 |

## Checking with the script

[scripts/conflict_register.py](../../scripts/conflict_register.py) uses only the Python standard library and runs on Python 3.9 or newer, with nothing else to install. Its tests have been run on Linux with Python 3.9, 3.11, 3.12 and 3.13. It has not been verified on Windows or macOS, where `python3` in the commands may need to be replaced with `py` or `python`.

The commands below are all run from the root of the repository and check the `examples/help-center` example; copy them and they run. To check your own project, replace the register and the folders. `-I` keeps Python from being affected by environment variables and by files of the same name next to the script, and `-B` stops it from writing `__pycache__`. The help text and error messages are in Chinese; when the usage is wrong, the `usage:` lines are the English built into Python's argparse.

```text
python3 -I -B scripts/conflict_register.py --help
```

### check: check the register

```text
python3 -I -B scripts/conflict_register.py check examples/help-center/conflict-register.json --texts-root examples/help-center
```

`--texts-root` is the folder that deliverable paths start from. The output is a JSON object:

- `status`: `OK` or `FAIL`; `problems`: one sentence per problem.
- `warnings`: what was not checked, and what may have been written wrong. Without `--texts-root` (when the register lists deliverables), the line numbers and original wording on the deliverable side are not checked, and a reminder appears here. For sources that are external references or have no `file`, their original wording cannot be checked, and this says that the N quotes citing the source were not checked ("引它的 N 处原句没有核"). A local source that was read without a `sha256`, a source with no local file that has a `sha256`, and keys the program does not know each get a reminder too. `warnings` does not affect the exit code.
- `counts`: the number of items in each status; `kinds`: the number of items of each kind.
- `sources`: how many sources are in force, superseded and pending; `stale` lists the ids of sources that have changed since they were registered; `digests` gives the current digest of each local source that was read.
- `texts_checked`: whether the deliverable side was checked.

The full output for the example is in [examples/README.md](../../examples/README.md) (in Chinese). If someone changes the original text of a pinned rule (here, in a temporary copy of the example, the characters "，语气亲切" ("in a friendly tone") were added before the full stop of item 2 of section 1 of the writing guide v2, "退款类文章也用“你”。"), `check` exits with 1 and reports:

```text
来源 writing-guide-v2：rules/writing-guide.md 在登记之后改过（登记的 sha256 是 08e4f08ebbdc326d64f07406cb9be8b1d941eab6bf45a271de066e023008407a，现在是 f3dc52f7f49125a99684bb895356ba10a25cdbf5875526a5166f282e578ba4a9）；先重核引用它的条目，再更新 sha256
```

*Translator's note:* in English: "Source writing-guide-v2: rules/writing-guide.md has changed since it was registered (the registered sha256 is 08e4…407a, now it is f3dc…a4a9); first re-check the items that cite it, then update sha256".

Changing only the annotation at the top of the file is not reported.

### list: list the items, giving the principal a decision sheet

```text
python3 -I -B scripts/conflict_register.py list examples/help-center/conflict-register.json --status open --markdown
```

- `--status` takes `open` (the default), `decided`, `closed` or `all`.
- Without `--markdown`, it outputs a JSON list made of the items as they are.
- With `--markdown`, it outputs a decision sheet. The first line is "## 项目名：还没定的条目（共 N 条）" ("## project name: items not yet decided (N in total)"); for `decided`, `closed` and `all` it says "已定的条目" (decided items), "已关闭的条目" (closed items) and "全部条目" (all items) instead. Each item gets one line with its id, kind, status and title, and either what the principal needs to decide (for items not yet decided) or how it was decided (for decided and closed items). Below that come, in order, what to do until it is decided, the original wording and location of each side (where a rule side has `strength`, "（必须）" ("(must)") or "（建议）" ("(recommendation)") is shown after the location; a value other than `must` or `should` is shown as written in JSON, as "（strength 写的是 …，先跑 check）" ("(strength is written as …; run check first)"), so that a wrong value does not look like a right one), the AI's proposal, and who decided it. When there are no items it writes "没有。" ("None."). Line breaks inside values are replaced with "／" in the sheet, so that continuation lines do not escape the list item. The sheet shown in "When it cannot be decided" above is its output.
- `list` only checks the top level, `schema`, and whether `items` is a list of objects, nothing else, so run `check` first.

### collide: check whether a new term is already used in the accepted deliverables

```text
python3 -I -B scripts/conflict_register.py collide --register examples/help-center/conflict-register.json --texts-root examples/help-center 标签 收藏
```

*Translator's note:* 标签 ("tag") and 收藏 ("favorites") are the two words being searched for in the example.

- It searches only the deliverables registered in `texts`, not the rule files.
- It searches for literal substrings, case-sensitive by default; add `--ignore-case` to ignore case. It does not split words: searching for `work` also matches `workspace`. It does not recognize inflected forms or synonyms. A word given twice counts once.
- It outputs JSON. In `words`, each word maps to a list of hits (which deliverable, which line, and the content of that line; for a long line only 40 characters on each side of the hit are kept, and the cut-off places are marked with "…"). `texts` is all the registered deliverables, `checked` those that were read, `missing_texts` those that were not found, and `unreadable_texts` those that could not be read (for example, not UTF-8).
- `complete` is `true` only when every registered deliverable was read. When it is `false`, "no hits at all" does not count.
- Whether a hit means the same thing, the program cannot judge; a person has to look.

### Exit codes

| Exit code | When |
| --- | --- |
| 0 | `check` found no problems; `list` produced its list; `collide`'s `complete` is `true` (0 whether or not there are hits) |
| 1 | `check` found any problem; the register is not found, is a folder, is not UTF-8, is not standard JSON (including `NaN` or unpaired escapes such as `\uD800`), is nested too deeply, has a top level that is not an object, or has the wrong `schema`; `list` meets `items` of the wrong shape; `collide` has deliverables that are not found, not UTF-8 or unreadable, `--texts-root` is not a folder, or `texts` is empty or not an object. In all these cases it outputs JSON explaining why, without a Python traceback |
| 2 | Wrong usage: a missing argument, a wrong value for `--status`, an empty `--texts-root`, or a word to search for in `collide` that is empty or has bytes that cannot be decoded as UTF-8 |

When a file is not UTF-8, the error message says which file, which line, and from which byte it cannot be read. Save it as UTF-8 and check again.

### What it can and cannot check

It can check:

- Whether the register's structure and required fields are complete, and of the right types.
- Whether the cited sources and deliverables are all registered.
- Whether chains of supersession end at a source that is in force or pending.
- Whether the original text of source files with a pinned `sha256` has changed.
- Whether the rule side's original wording is in the original text, whether the deliverable side's original wording is on the stated line, and whether the line number is out of range.
- Where a rule side has `strength`, whether its value is `must` or `should`; whether a deliverable side has `strength` written by mistake.
- Whether decided items state who decided and on what basis: the words of the principal, or of the person they authorized, and where they came from, or which of steps 1 to 4 the AI used; whether an `exception` was decided by the principal.
- On which lines of which deliverables a new term is used, and whether every registered deliverable was read.

It cannot check:

- Whether the rules are well written, whether they should stay, or which of two rules is right.
- How the principal should decide; whether the `rule_applied` the AI wrote really applies (it only checks that it is an integer from 1 to 4); whether a rule really is a must or a recommendation (it only checks how `strength` is written); whether `resolution`, `meanwhile` and `ask` are right (it only checks that they are non-empty).
- The original wording in external references and in sources without `file`.
- Whether the deliverables themselves are right.
- Whether a `collide` hit means the same thing; files not registered in `texts`.
- Date formats (it only checks that dates are non-empty).

Also note: paths in the register are not confined to the starting folder; absolute paths, paths starting with `../` and symbolic links pointing outside are read as written. When you run it on a register someone else gave you, it will read any local file the register names: `collide` writes whole matching lines into its output, and `check` gives the digest of each file it read and says whether the original wording is in it. First look at which paths the register lists; the same applies when you have an AI run someone else's register for you.

A passing `check` only shows that what the register itself says matches the files it names. It does not show that these conflicts were decided correctly, nor that this approach will certainly make the work better.
