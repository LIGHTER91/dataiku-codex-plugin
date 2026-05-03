# Dataiku Flow Architect

Use this skill to reason about the architecture of a Dataiku Flow.

## Tasks

- build dependency graph.
- detect unnecessary complexity.
- suggest modularization.
- identify missing zones.
- separate ingestion, transformation, ML, RAG and reporting.
- recommend naming conventions.
- identify technical debt.
- recommend Flow documentation structure.

## Tool strategy

Use:

1. `dataiku_get_flow_graph`
2. `dataiku_analyze_flow_health`
3. `dataiku_generate_project_map`
4. `dataiku_generate_flow_documentation`

## Architecture smells

- too many objects in a single zone.
- unclear naming.
- duplicated processing branches.
- manual intermediate datasets.
- recipes with many inputs/outputs.
- missing final outputs.
- hidden dependencies.
- no clear RAG/ML boundary.

## Expected report format

```md
# Flow Architecture Review

## Current architecture
...

## Dependency graph summary
...

## Architecture issues
...

## Proposed restructuring
...

## Naming and zoning recommendations
...
```
