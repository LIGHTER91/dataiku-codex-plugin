# Data Privacy Specification

## Privacy goals

The plugin must avoid exposing sensitive data from Dataiku DSS.

## Default behavior

- Return metadata, not full data.
- Preview small samples only.
- Redact secrets.
- Limit file reads.
- Limit logs.
- Avoid connection details.
- Never request sensitive info by default.

## Dataset privacy

Dataset preview must:

- use a small default row limit.
- support maximum configured limit.
- redact sensitive-looking columns.
- avoid returning large text blobs by default.
- avoid returning binary content.
- warn the user if data may contain PII.

## Sensitive column names

The redaction layer should treat these as sensitive by default:

- password
- passwd
- token
- api_key
- secret
- access_key
- private_key
- email
- phone
- address
- ssn
- iban
- credit_card
- card_number
- user_id if configured
- employee_id if configured

## Logs privacy

Logs may contain secrets. The plugin must:

- redact tokens.
- redact credentials.
- redact connection strings.
- truncate long logs.
- avoid returning environment dumps.

## Recipe code privacy

Recipe code may contain hardcoded secrets. The plugin must:

- detect secret-looking assignments.
- redact values.
- keep line numbers if possible.
- report that a secret may exist without revealing the secret.

## Managed Folder privacy

File reading must:

- be size-limited.
- detect binary files.
- support explicit max bytes.
- redact secrets in text files.
- avoid returning full datasets stored as files.

## Audit privacy

Audit logs must not contain:

- API keys.
- data rows.
- file contents.
- raw logs.
- secret-looking values.
- credentials.
