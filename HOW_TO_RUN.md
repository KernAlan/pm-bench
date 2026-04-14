# How to run PM-Bench

A step-by-step walkthrough for a new user. If you just want the TL;DR, see the Quickstart block in [README.md](README.md).

---

## 1. Clone the repo

```bash
git clone https://github.com/KernAlan/pm-bench.git
cd pm-bench
```

---

## 2. Install

PM-Bench is packaged as a normal Python project. Python 3.10+ is required.

```bash
# Editable install with every optional extra (runner + analysis tooling).
pip install -e ".[all]"

# Or install just what you need:
pip install -e ".[anthropic]"    # only Claude
pip install -e ".[openai]"       # only OpenAI
pip install -e ".[analysis]"     # pandas/scipy/numpy for the analyzers
pip install -e ".[dev]"          # pytest for contributors
```

After installation, a `pm-bench` command is available:

```bash
pm-bench --help
```

It is an alias for `python run.py` and takes the same arguments.

### Alternative: run in Docker

If you'd rather not touch your host Python environment, PM-Bench ships a
`Dockerfile` and `docker-compose.yml` that pin a reproducible runtime.

```bash
# Build the image (installs ".[all]" inside the container)
docker build -t pm-bench .

# Offline demo — no API key needed
docker run --rm pm-bench python demo.py --no-color

# End-to-end mock pipeline (deterministic, no API key needed)
docker run --rm pm-bench python run.py --provider mock --superhuman-only

# Real run — mount results/ so files persist on the host
docker run --rm \
    -e ANTHROPIC_API_KEY \
    -v $(pwd)/results:/app/results \
    pm-bench python run.py --superhuman-only

# Or via docker-compose
ANTHROPIC_API_KEY=sk-ant-... docker compose run --rm pm-bench
```

The image includes a `HEALTHCHECK` that runs `demo.py --no-color` to catch
broken builds quickly.

---

## 3. Set your API key

Pick the provider(s) you want to run against:

```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
export OPENAI_API_KEY=sk-...

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

Cross-family judging (scoring Claude with GPT or vice versa) requires both keys.

---

## 4. Try the offline demo first

`demo.py` runs a couple of scenarios with a deterministic stub "model" that does not call any API. This is the fastest way to verify your install.

```bash
python demo.py
```

Expected output: a pretty-printed run over 2–3 scenarios with a score summary. No network, no cost.

### Mock provider (full pipeline, no API key)

For a complete end-to-end pipeline check — argument parsing, context
assembly, scoring, result persistence — use the built-in `mock` provider:

```bash
python run.py --provider mock --superhuman-only            # 100% (perfect)
python run.py --provider mock --mock-mode random           # ~25% baseline
python run.py --provider mock --mock-mode weak             # 0% (failure path)
python run.py --provider mock --mode open-ended --scenario 1
```

`--mock-mode perfect` (default) returns the correct answer for every
scenario; `random` returns a deterministic pseudo-random letter seeded
by scenario id; `weak` returns a wrong answer. Useful for CI, smoke
tests, and reproducing pipeline bugs without burning tokens.

---

## 5. Run a single scenario

Useful for debugging a specific item or inspecting prompts.

```bash
python run.py --scenario 49 --provider anthropic --model claude-sonnet-4-20250514
```

Replace `49` with any scenario id from `scenarios/scenarios.json`. Use `--dry-run` to print the assembled prompt and exit without calling the API.

---

## 6. Run the Superhuman 20 with multiple iterations

The core benchmark is the 20 scenarios in the `Superhuman PM Judgment` category. Running them multiple times captures run-to-run variance (temperature noise, tool-call nondeterminism).

```bash
python tools/multi_run.py \
    --iterations 3 \
    --models claude-sonnet-4-20250514 \
    --modes mcq \
    --superhuman-only
```

This produces per-iteration result JSON files in `results/` and an aggregate summary with confidence intervals.

---

## 7. Run open-ended with a cross-family judge

Open-ended scenarios are scored by an LLM judge against a rubric. Using a *different model family* as the judge reduces self-preference bias.

```bash
python run.py \
    --mode open-ended \
    --provider anthropic \
    --model claude-sonnet-4-20250514 \
    --judge-provider openai \
    --judge-model gpt-4o
```

The judge sees the rubric and the response, emits a PASS/FAIL with a cited sentence, and the runner aggregates judge verdicts.

---

## 8. Analyze results

After one or more runs, the analyzer computes difficulty, discrimination, and per-category breakdowns.

```bash
python tools/analyze.py
```

Output goes to stdout and to `results/analysis/` (summary tables, per-category plots if `matplotlib` is installed).

For a single-run markdown report with per-category ASCII bar charts and
pass/fail detail, use `tools/report.py`:

```bash
python tools/report.py results/20260414-120000_mcq_anthropic_claude-sonnet-4.json
```

It prints to stdout and writes a companion `*_report.md` next to the
results JSON. No extra dependencies.

---

## 9. Validate the answer key with multiple models

Before trusting a scenario's `correct_answer`, sanity-check it against several top models. If no strong model gets it right, the answer key is probably wrong or the scenario is broken.

```bash
python tools/validate_answers.py \
    --models claude-sonnet-4-20250514 gpt-4o claude-opus-4-5
```

This prints a table of scenarios where models disagree with the answer key.

---

## 10. Check for contamination

Test whether a given model has memorized the dataset. Contamination checks compare the model's behavior on canonical vs. variant workspaces.

```bash
# First, generate a workspace variant (see tools/workspace_variants.py):
python tools/workspace_variants.py --variant v2-neon

# Then run contamination analysis:
python tools/contamination.py --model claude-sonnet-4-20250514
```

A big accuracy drop between the canonical and variant runs is a contamination signal. A near-identical score is evidence the model is generalizing.

---

## 11. Submit your results

1. Fork the repo.
2. Add your run JSON under `submissions/<your-name>/<date>/`.
3. Update `LEADERBOARD.md` with a row for your model.
4. Open a PR. See `CONTRIBUTING.md` and `SUBMISSIONS.md` for the exact format.

---

## Expected costs & runtime

These are ballpark figures for one full run (68 MCQ + 20 open-ended with a cross-family judge). Tokens include the workspace context (~6k per scenario average).

| Model                       | Input tokens | Output tokens | Est. cost | Wallclock |
|-----------------------------|--------------|---------------|-----------|-----------|
| claude-sonnet-4-20250514    | ~550k        | ~22k          | ~$1.80    | ~8 min    |
| claude-opus-4-5             | ~550k        | ~22k          | ~$9.00    | ~10 min   |
| gpt-4o                      | ~550k        | ~22k          | ~$2.70    | ~6 min    |
| gpt-5 (reasoning)           | ~550k        | ~80k          | ~$12.00   | ~20 min   |

Multiply by your iteration count. The Superhuman 20 subset is roughly 30% of the full benchmark by token count.

---

## Troubleshooting

**`pm-bench: command not found`** — run `pip install -e .` inside the repo root, or invoke `python run.py` directly.

**`ModuleNotFoundError: No module named 'anthropic'`** — you installed without the optional extra. Re-install with `pip install -e ".[anthropic]"` or `".[all]"`.

**Rate-limit errors from Anthropic / OpenAI** — pass `--concurrency 1` to `run.py`, or use `tools/multi_run.py` which paces requests automatically.

**A scenario fails with "fixture not found"** — you are running against a variant scenarios file but the variant's fixture tree hasn't been generated. Run `python tools/workspace_variants.py --variant <v>` first.

**Judge returns nonsense verdicts** — check that you passed a capable judge model (`gpt-4o` / `claude-sonnet-4` or better). Smaller models do not follow the rubric format reliably.

**Schema validation failure** — run `python tools/validate_schema.py` for the full error list; every issue points at a specific scenario id.
