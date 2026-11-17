# Runtime contract

Infer the user's requested action first, then call the selector with the declared intent and domain. The selector returns `route`, `domain`, `depth` (`quick` or `structured`), a built-in `method`, suggested `checks`, and optional upstream `modules`. These suggestions help prepare a plan; use the user's actual criteria and record applicable checks in the checkpoint. Software module names are informational. The selector needs no external modules.

Choose one of `software`, `creative`, `research`, `documents`, `data`, `operations`, or `general`. A custom domain follows the same format as `museum-collections` and receives the general checks for the chosen intent. Use `--complex` when there are real dependencies, multiple verification steps, or handoffs. Complexity does not change what action was requested.

The evaluator is read-only. Keep checkpoint JSON in the task's own authorized working area. Collect real command receipts and review evidence before creating records. The evaluator validates the supplied fields and their relationships. The host verifies receipt provenance, review quality, and tool permissions.

## Commands

Run these relative to the skill directory, using absolute task file paths where convenient.

```bash
python3 scripts/workflow.py route --intent repair --domain software --complex
python3 scripts/workflow.py fingerprint /absolute/path/source.txt /absolute/path/export.txt
python3 scripts/workflow.py evaluate /absolute/path/checkpoint.json
```

`fingerprint` returns SHA-256 hex strings indexed by the input paths. Copy the hashes into stable logical keys such as `source` and `artifact`. At resume, recompute hashes for changed or potentially changed files. Record exact versions for other relevant inputs such as criteria, test suite, or review standard.

## Checkpoint example

The values below illustrate the schema. Replace them with actual records.

```json
{
  "versions": {
    "source": "source-version-1",
    "artifact": "candidate-version-2",
    "criteria": "criteria-version-1",
    "tests": "suite-version-3"
  },
  "checks": [
    {"id": "source-fidelity", "kind": "review", "depends_on": ["source", "artifact", "criteria"]},
    {"id": "export-test", "kind": "test", "depends_on": ["artifact", "tests"]}
  ],
  "evidence": {
    "source-fidelity": {
      "result": "PASS",
      "versions": {"source": "source-version-1", "artifact": "candidate-version-2", "criteria": "criteria-version-1"},
      "reference": "review.md#source-fidelity",
      "context_isolation": "shared"
    },
    "export-test": {
      "result": "PASS",
      "versions": {"artifact": "candidate-version-2", "tests": "suite-version-3"},
      "reference": "test-report.txt",
      "exit_code": 0,
      "executed": 2
    }
  },
  "revision_count": 1,
  "max_revisions": 3,
  "retry_count": 0
}
```

- Define at least one required check. Each check declares one or more version keys. Use `required: false` for an optional check. Record deliberate scope and criteria changes separately.
- Use `kind: "test"` when a runner reports the executed test count and exit code. `executed` counts tests that ran, excluding cases that were only collected, selected, or skipped. Use `mechanical` for a recorded deterministic check and `review` for a human or model judgment.
- Receipts use `PASS`, `FAIL`, or `NOT_APPLICABLE`. The last requires explicit `allow_not_applicable: true` in the check plan and an evidence reason. Leave missing results absent.
- For an independent-context requirement use `requires_isolation: true` on the review check. Record `context_isolation` based on what happened. A shared or unknown context does not satisfy it.
- Before an external action add `external_action` with `action`, `target`, `artifact_ref` and `artifact_version`. The artifact reference must name a current version used by a required check. Include `approval` with matching action, target, artifact version, and a `reference` to the real user authorization. Recheck actual host permissions and any finer authorization limits at execution time. To evaluate a draft separately, omit the external action.
- Use `stop_reason` when a stop was requested or the next step would exceed the applicable budget or boundary. Use `blocked_reason` for a necessary resource or decision that cannot currently be obtained. Keep revision and retry counters between runs. The evaluator reports counters as supplied, and the operator records increments only for real attempts.

## Decision and resume

| Status | Meaning |
|---|---|
| `READY` | Required checks are current and satisfied for the stated operation |
| `RECHECK` | The listed required checks lack usable evidence or are stale |
| `REVISE` | A required check failed and revision budget remains |
| `BLOCKED` | A required version, input, capability, decision or authorization is missing |
| `STOPPED` | A stop condition applies or a required failure remains at the revision limit |

On resume, retain prior receipts and update the current version keys. Refresh the IDs in `recheck`, using their declared dependencies. Keep unaffected evidence and counters. An old receipt never becomes current by editing only its version label. Preserve the audit trail and save the new receipt after verification.

A return code of zero from this program means that a decision was produced. Read the JSON `status` to determine the decision. A failing validation or unreadable input returns a nonzero code.
