# Dataiku Code Environment Doctor

Use this skill for Python/R package, dependency, offline install, native library, model loading or code environment problems.

## Checks

- missing packages.
- incompatible versions.
- wrong Python version.
- native dependency errors.
- package installed outside code env.
- offline wheel issues.
- Hugging Face/local model path issues.
- CUDA/GPU package mismatch.
- imports failing in recipes.

## Tool strategy

Use:

1. `dataiku_list_code_envs`
2. `dataiku_get_code_env_details`
3. `dataiku_code_env_doctor`
4. `dataiku_get_recipe_details` if linked to a recipe failure.
5. `dataiku_get_job_logs` if linked to logs.

## Expected report format

```md
# Code Environment Diagnosis

## Environment
...

## Symptoms
...

## Dependency issues
...

## Recommended installation/fix
...

## Reproducibility recommendations
...
```
