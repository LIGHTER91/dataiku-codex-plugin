# Dataiku ML Command Orchestrator

Use this skill when the user wants to launch a repeatable ML setup quickly from natural language.

## Product rule

- prefer reusable ML commands over generated setup scripts
- prefer Dataiku visual components over custom Python when DSS already has a native component
- only fall back to direct code edits for narrow maintenance work such as renames or targeted fixes

## Tool strategy

Use:

1. `dataiku_suggest_prediction_targets`
2. `dataiku_list_ml_commands`
3. `dataiku_plan_ml_command`
4. `dataiku_run_ml_command`

## Expected flow

1. identify the dataset
2. propose likely prediction targets when the user did not specify one
3. pick the closest catalog command
4. show the planned Prepare recipe and Visual ML task
5. request or use explicit approval before execution

## Expected response style

- emphasize the visual assets that will be created in DSS
- avoid proposing new setup scripts for recurring ML workflows
- if no catalog command fits, explain the gap and only then discuss a code fallback
