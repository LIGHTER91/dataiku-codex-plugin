# Dataiku Scenario Debugger

Use this skill for failed scenarios, jobs and automation problems.

## Tasks

- inspect scenario runs.
- read logs.
- identify failed steps.
- explain root cause.
- suggest fix.
- recommend retry/rollback strategy.
- distinguish code, data, dependency and permission failures.

## Tool strategy

Use:

1. `dataiku_list_scenarios`
2. `dataiku_get_scenario_runs`
3. `dataiku_get_job_logs`
4. `dataiku_explain_failure`
5. related dataset/recipe/folder tools depending on failure.

## Common causes

- missing input dataset.
- schema mismatch.
- package missing in code env.
- Managed Folder file not found.
- permission issue.
- timeout.
- memory error.
- LLM connector failure.
- vector store failure.

## Expected report format

```md
# Scenario Failure Analysis

## Failed run
...

## Error summary
...

## Evidence from logs
...

## Probable root cause
...

## Fix
...

## Retry strategy
...
```
