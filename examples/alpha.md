# Alpha Design Rules

The cache expires after thirty minutes of inactivity.
All retries use exponential backoff with a ceiling of five attempts.

## Storage

Records are stored as append-only entries.
Corrections are written as new entries that supersede the old ones.

## Naming

Every public function name begins with a verb.
