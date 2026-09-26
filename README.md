# Political You — Current Statements

This public repo holds the **approved monthly statements** shown in the Political You app's *Current Statements* section. Each batch contains short, dated, sourced public statements from the four parties (Green, Libertarian, Democratic, Republican) on each of the app's 7 quiz topics.

The app downloads one static file:

- **Feed:** `https://nightcrawler-dev.github.io/political-you-statements/current.json`
- **Schema:** [`current.schema.json`](current.schema.json) (JSON Schema draft 2020-12), also served at `https://nightcrawler-dev.github.io/political-you-statements/current.schema.json`

There is no `current.json` yet. Until the first approved batch is merged, the app gets a 404 and keeps its bundled copy. The app treats a missing file, a failed download and a file with `"published": false` the same way: it ignores them.

## How a batch is approved

1. Draft `current.json` on a new branch, following the schema. Set `batchMonth` (e.g. `"2026-10"`), `"published": true` and `"sample": false`.
2. Run `pip install jsonschema` and `python3 tools/validate_statements.py current.json`, then fix every ERROR.
3. Open a pull request titled "Statements for <Month Year>". The **Validate statements** check runs on every pull request.
4. The owner reviews the quotes against their sources. **Merging the pull request to `main` is the approval.** GitHub Pages publishes it within a few minutes, and phones pick it up on their next launch.

## Rules for every batch

- **Balance:** every one of the 7 topics has all four parties, with the same number of statements per party, either 1 each or 2 each (28–56 statements in total). A missing topic or party fails the check.
- **Exact words:** quotes are copied word for word. Cuts are marked with an ellipsis (…). No paraphrases.
- **Sourced and dated:** every statement has an `https` source link, the statement's `date`, and `verifiedAt` (the day the quote was checked against the source). Dates should be within about 12 months of the batch month.
- Topics (`topicId`): `courts-justices`, `safety-security`, `trust-democracy`, `jobs-prices`, `borders-immigration`, `health-care-access`, `abortion-choice`.
- Parties (`partyId`): `green`, `libertarian`, `democratic`, `republican`.
- Statement ids follow `<batchMonth>-<topicId>-<partyId>-<n>`, e.g. `2026-10-courts-justices-green-1`.

## Example

```json
{
  "schemaVersion": 1,
  "batchMonth": "2026-10",
  "published": true,
  "sample": false,
  "statements": [
    {
      "id": "2026-10-courts-justices-green-1",
      "topicId": "courts-justices",
      "partyId": "green",
      "speaker": "Name of the person or body quoted",
      "speakerTitle": "Their role at the time",
      "quote": "Exact words from the source, without quotation marks.",
      "date": "2026-10-03",
      "sourceUrl": "https://example.org/source",
      "sourceTitle": "Page or document title (publisher)",
      "verifiedAt": "2026-10-20"
    }
  ]
}
```

Only public statements from public sources belong here. The schema and validator are copies of the ones in the app's (private) repository and are kept in sync with it.
