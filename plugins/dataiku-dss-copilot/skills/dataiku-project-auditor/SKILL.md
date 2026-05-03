# Dataiku Project Auditor

Use this skill when the user asks to understand, audit or summarize a Dataiku DSS project.

## Responsibilities

- Inspect project structure.
- Summarize datasets, recipes, scenarios and Managed Folders.
- Build a mental model of the Flow.
- Identify risks and missing documentation.
- Produce clear reports.
- Recommend next debugging or documentation steps.

## Tool strategy

Use:

1. `dataiku_get_project_summary`
2. `dataiku_get_flow_graph`
3. `dataiku_list_datasets`
4. `dataiku_list_recipes`
5. `dataiku_list_managed_folders`
6. `dataiku_list_scenarios`
7. `dataiku_analyze_flow_health`

## Safety rules

- Prefer read-only tools.
- Do not modify anything.
- Do not preview data unless needed.
- Keep report evidence-based.
- Warn when permissions limit the analysis.

## Expected report format

```md
# Dataiku Project Audit

## Summary
...

## Flow architecture
...

## Main objects
...

## Risks
...

## Recommendations
...
```

## Example user requests

- "Analyze my Dataiku project PROJECT_KEY."
- "Explain the architecture of this Dataiku Flow."
- "Find technical debt in my Dataiku project."
