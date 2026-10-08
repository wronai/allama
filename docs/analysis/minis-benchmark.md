# Minis Ollama benchmark — 2026-10-08

Ticket: PLF-001. Branch: `ticket/001-minis-benchmark`.
Base: `c8cfea5f81964a060ad81cc8222f952976f80f37`.

## Discovery and baseline

The project was located using semcod/search. The live search service was healthy;
the conversation's MCP transport had expired. A fresh MCP client initialized and
successfully called `search_projects`. Indexing the missing `wronai` organization
added/refreshed 72 projects without failures. No search source changes were needed.

Allama's existing `LLMTester.test_model` ran its default addition prompt against
`gpt-oss:20b` on `http://minis:11434`: 17.158 seconds, valid syntax and successful
execution. Inspection found that `think=low` and `think=false` were dropped,
`success` meant HTTP success, and function definitions could pass execution without
being called. That baseline is not a functional quality score.

## Implementation

`allama benchmark` is an explicit native Ollama profile within this project. It
reuses `CodeEvaluator` for extraction and `ReportGenerator` for HTML generation.
The original CSV CLI remains available; its thinking forwarding was corrected.

- Six Polish coding tasks with concrete assertions, including unhashable values,
  mutation, invalid inputs, Decimal arithmetic, cycles and zero-capacity LRU.
- Two repeats per model, deterministic shuffled task order; temperature 0, seed 42,
  context 8192, maximum 1024 generated tokens. Same prompts and limits for all.
- Lowest-overhead advertised thinking mode: `false` if supported, otherwise `low`
  if supported; omit when metadata is absent. This compares practical fast modes,
  not equal reasoning budgets. GPT-OSS reasoning cannot be switched off here.
- One model resident at a time. Warm-up/load recorded separately. Timing includes
  stream completion; first output and first answer content are separate metrics.
- Tokens/s = `eval_count / (eval_duration / 1e9)`. This includes reasoning; differing
  tokenizers make whole-answer latency necessary alongside throughput.
- Truncation, missing completion, empty content and transport errors fail the trial.
  Functional errors remain in the quality denominator. Timing medians use complete,
  non-empty, non-truncated answers, including functionally wrong answers.
- Generated code runs in a pinned Python 3.12 Docker image without network,
  writable host mounts, root privileges or Linux capabilities; memory/CPU/process
  and wall-time limits apply. Completion marker rejects early `SystemExit(0)`.
- Every attempt saves JSON atomically and regenerates an escaped, offline HTML
  report. Existing result directories cannot be overwritten accidentally.

## Reproduce

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e . 'pytest>=8,<9'
docker pull python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
.venv/bin/python -m pytest tests -q
.venv/bin/allama benchmark --url http://minis:11434 \
  --models gpt-oss:20b qwen3.5:9b gemma4:12b qwen3.8:27b devstral-small-2:24b \
  --repeats 2 --context 8192 --limit 1024 --unload-existing \
  --host-label 'minis · Ryzen 9 7940HS · Radeon 780M · 46 GiB RAM' \
  --output benchmark-results
```

`--unload-existing` explicitly allows evicting models from Ollama memory; run when
no one else is using this inference server. It does not delete model files.
Model names identify local installations; full digests and model metadata are in
JSON. No release-date or vendor identity claim is inferred solely from a tag.

## Limits

This is a small diagnostic suite, not a general intelligence benchmark. Repeats
measure consistency and latency, not independent quality samples. LRU asymptotic
complexity is requested but not proved by the assertions. Long context, tool use,
vision, energy consumption and concurrent serving are not measured.

Memory is the model allocation reported by `/api/ps`, not peak machine RAM or
power consumption. Radeon 780M shares system memory. The host has approximately
46 GiB available physical memory; this does not simulate a computer with 16 GiB
total RAM. The reported GPU allocation can be compared with a 16 GiB budget.

## Evidence and delivery

Runtime evidence: `/home/tom/.local/state/minis-allama-20261008/`.
Browser report: `http://minis:3001/` (minis user unit `allama-benchmark-report`).
Final result summary and verification are added after the run completes.

API definitions: [Ollama chat](https://docs.ollama.com/api/chat),
[thinking controls](https://docs.ollama.com/capabilities/thinking).
