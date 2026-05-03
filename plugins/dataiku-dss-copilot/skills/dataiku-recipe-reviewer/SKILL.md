# Dataiku Recipe Reviewer

Use this skill to review Python, SQL, PySpark or visual recipe settings.

## Review criteria

- correct use of Dataiku API.
- memory usage.
- logging.
- error handling.
- inputs/outputs.
- schema handling.
- code env dependencies.
- reproducibility.
- readability.
- maintainability.

## Tool strategy

Use:

1. `dataiku_list_recipes`
2. `dataiku_get_recipe_details`
3. `dataiku_review_recipe_code`
4. `dataiku_get_dataset_schema`
5. `dataiku_code_env_doctor` if dependency issue suspected.

## Dataiku-specific checks

- bad Managed Folder path assumptions.
- hardcoded project keys.
- hardcoded dataset names where avoidable.
- missing output schema handling.
- batch size too large.
- loading entire dataset in memory.
- improper use of Dataiku APIs.

## Expected report format

```md
# Recipe Review

## Recipe
...

## Strengths
...

## Issues
...

## Risk level
...

## Suggested patch
...
```

## Example user requests

- "Review this Python recipe."
- "Find bugs in recipe X."
- "Refactor my Dataiku recipe."
