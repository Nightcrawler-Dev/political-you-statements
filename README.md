# Political You — Current Statements

This public repo holds the **approved monthly statements** shown in the Political You app's *Current Statements* section. Each batch contains short, dated, sourced public statements from the four parties (Green, Libertarian, Democratic, Republican) on the app's 7 quiz topics.

The app downloads one static file:

- **Feed:** `https://nightcrawler-dev.github.io/political-you-statements/current.json`
- **Schema:** [`current.schema.json`](current.schema.json) (JSON Schema draft 2020-12), also served at `https://nightcrawler-dev.github.io/political-you-statements/current.schema.json`

There is no `current.json` yet. Until the first approved batch is merged, the app gets a 404 and keeps its bundled copy. The app treats a missing file, a failed download and a file with `"published": false` the same way: it ignores them.

## How a batch is approved

1. Draft `current.json` on a new branch, following the schema. Set `batchMonth` (e.g. `"2026-10"`), `"published": true` and `"sample": false`.
2. Run `pip install jsonschema` and `python3 tools/validate_statements.py current.json`, then fix every ERROR.
3. Open a pull request titled "Statements for <Month Year>". The **Validate statements** check runs on every pull request.
4. **Independent review.** A checker separate from the collector re-verifies every quote, date, title and context against the source. It scores each topic 1–5 for same issue, speaker prominence, and tone, and anything at 2 or below is fixed or the topic is dropped. The scorecard is saved as `reviews/<batchMonth>.md` in the same pull request.
5. When the review and the check both pass, the pull request is squash-merged. Approval is delegated by the owner, who gets a summary afterward. GitHub Pages publishes it within a few minutes, and phones pick it up on their next launch.

## Rules for every batch

- **Balance: a topic is all four parties or none.** A topic may be left out for a month. A topic that is present has all four parties, with the same number of statements per party, either 1 each or 2 each. A topic with a missing party fails the check, and so does a batch with no topics (so 4–56 statements). The app shows an absent topic as "No statements for this topic this month."
- `batchMonth` may be next month, so a batch can be prepared late in the month before.
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
