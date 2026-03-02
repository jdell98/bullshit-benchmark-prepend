<h1>
  <img src="docs/images/bsbench.png" alt="BullshitBench logo" width="64" />
  BullshitBench
</h1>

BullshitBench measures whether models detect nonsense, call it out clearly, and avoid confidently continuing with invalid assumptions.

- Public viewer (stable): https://petergpt.github.io/bullshit-benchmark/viewer/index.html
- Public viewer (v2-focused): https://petergpt.github.io/bullshit-benchmark/viewer/index.v2.html
- Updated: 2026-03-01

![BullshitBench Results](docs/images/bullshit-benchmark-results.png)

![BullshitBench Viewer Chart (Screenshot)](docs/images/viewer-chart-screenshot.png)

## Benchmark Scope (v2)

- `100` nonsense prompts total.
- `5` domain groups: `software` (40), `finance` (15), `legal` (15), `medical` (15), `physics` (15).
- `13` nonsense techniques (for example: `plausible_nonexistent_framework`, `misapplied_mechanism`, `nested_nonsense`, `specificity_trap`).
- `3`-judge panel aggregation (`anthropic/claude-sonnet-4.6`, `openai/gpt-5.2`, `google/gemini-3.1-pro-preview`) using `full` panel mode + `mean` aggregation.
- Published v2 leaderboard currently includes `72` model/reasoning rows.

## What This Measures

- `Clear Pushback`: the model clearly rejects the broken premise.
- `Partial Challenge`: the model flags issues but still engages the bad premise.
- `Accepted Nonsense`: the model treats the nonsense as valid.

## Quick Start

1. Set your API key:

```bash
export OPENROUTER_API_KEY=your_key_here
```

2. Run collection + primary judge (Claude by default):

```bash
./scripts/run_end_to_end.sh
```

3. Run v2 end-to-end and publish into the dedicated v2 dataset:

```bash
./scripts/run_end_to_end.sh --config config.v2.json --viewer-output-dir data/v2/latest --with-additional-judges
```

4. Optionally run the default config end-to-end (publishes to `data/latest`):

```bash
./scripts/run_end_to_end.sh --with-additional-judges
```

5. Open the viewer:

- Published viewer (stable): https://petergpt.github.io/bullshit-benchmark/viewer/index.html
- Published viewer (v2-focused): https://petergpt.github.io/bullshit-benchmark/viewer/index.v2.html
- Local viewer (optional):

```bash
./scripts/run_end_to_end.sh --with-additional-judges --serve --port 8877
```

Then open `http://localhost:8877/viewer/index.html`.
Use the `Benchmark Version` dropdown in the filters panel to switch between published datasets (for example `v1` and `v2`).

## v1 to v2

- v1 dataset remains in `data/latest`.
- v2 dataset is published in `data/v2/latest`.
- v2 question set comes from `drafts/new-questions.md` via `scripts/build_questions_v2_from_draft.py`.
- Canonical judging is now fixed to exactly 3 judges on every row with mean aggregation (legacy disagreement-tiebreak mode is retired from the main pipeline).
- Release notes and notable changes are tracked in `CHANGELOG.md`.

## Documentation

- [Technical Guide](docs/TECHNICAL.md): pipeline operations, publishing artifacts, launch-date metadata workflow, repo layout, env vars.
- [Changelog](CHANGELOG.md): v1 to v2 release notes and publish-history highlights.
- [Question Set](questions.json): benchmark questions and scoring metadata.
- [Question Set v2](questions.v2.json): v2 question pool generated from `drafts/new-questions.md`.
- [Config](config.json): default model/pipeline settings.
- [Config v2](config.v2.json): v2-ready config (uses `questions.v2.json`).

## Notes

- This README is intentionally audience-facing.
- Technical and maintainer-oriented content lives in `docs/TECHNICAL.md`.

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=petergpt/bullshit-benchmark&type=Date&theme=dark" />
  <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=petergpt/bullshit-benchmark&type=Date" />
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=petergpt/bullshit-benchmark&type=Date" />
</picture>
