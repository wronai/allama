# Minis Ollama benchmark — 2026-10-08

Ticket: PLF-001. Branch: `ticket/001-minis-benchmark`.
Base: `c8cfea5f81964a060ad81cc8222f952976f80f37`.

## Results

| Installed profile | Passed | Median answer | Median tokens/s | Memory observation |
|---|---:|---:|---:|---|
| gemma4:12b | 12/12 | 11.84 s | 25.87 | ~9.9 GiB VRAM+GTT increment |
| gpt-oss:20b | 12/12 | 14.77 s | 20.65 | 11.97 GiB API allocation |
| qwen3.8:27b | 12/12 | 26.05 s | 11.98 | 16.24 GiB API allocation |
| qwen3.5:9b | 8/12 | 29.27 s | 14.36 | 5.44 GiB API allocation |
| devstral-small-2:24b | 9/12 | 32.44 s | 5.74 | 14.76 GiB API allocation |

Gemma 4 12B was the fastest installed profile among those passing all 12 trials
(six tasks, two repeats). GPT-OSS and Qwen 27B also passed all trials. This is
evidence for this small coding suite and these settings, not general model superiority.

Gemma driver sampling measured a 9.942 GiB VRAM+GTT increment. Its API value of
1.243 GiB was rejected as inconsistent with driver and buffer evidence. Qwen 27B
reported 16.238 GiB allocation at context 8192, exceeding a strict 16 GiB budget.

Final reevaluation: 60/60 answers checked; zero unresolved infrastructure errors,
zero selected transport failures and zero truncated answers. All 48 regression
tests passed. Eleven DNS failures and four interfered trials remain in the JSON
audit history outside the selected 60-trial comparison.

[Standalone HTML report](minis-20261008/index.html) · [Raw JSON](minis-20261008/results.json)
· [AMD memory observations](minis-20261008/driver-memory.json)
· [Regression result](minis-20261008/tests.txt) · [Artifact checksums](minis-20261008/sha256.json)

### Functional failures

- qwen3.5:9b: topological_sort (2/2 failed), merge_intervals (1/2 failed), deep_merge (1/2 failed).
- devstral-small-2:24b: topological_sort (1/2 failed), deep_merge (2/2 failed).

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
- Container startup has a separate 60-second host deadline; code has a 10-second
  in-container alarm. Runtime startup failures are marked `infra_error`, excluded
  from the quality denominator and displayed as unscored.
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
Browser report: `http://minis:3001/` (minis user unit `allama-report`).
The final report and supporting evidence are archived alongside this document.

API definitions: [Ollama chat](https://docs.ollama.com/api/chat),
[thinking controls](https://docs.ollama.com/capabilities/thinking).


### Evaluator correction during the run

The extended regression run exposed a container-startup timeout on the busy
client host (load 25.5 with 16 logical CPUs). The original 12-second deadline
included Docker startup. Hostguard and fixos diagnostics were saved; no unrelated
processes were terminated. The evaluator now separates a 60-second launch deadline
from a 10-second code execution alarm, records infrastructure errors separately,
and includes failing assertion source in tracebacks. All saved answers were
reevaluated with this corrected evaluator, preserving `original_evaluation`.
Inference timings are not changed by reevaluation.

```bash
.venv/bin/allama benchmark --reevaluate benchmark-results
```

Protected code publication is pending: the deployed Validator registry has no
`wronai/allama` repository or OneDev profile. Its adoption requires the independent
controller. The checkpoint/outbox records this exact next action; no approval
checks were bypassed. Local report hosting is independent of code publication.

### Recovery and memory reporting

A transient DNS failure on the client interrupted the first run after 36 recorded
attempts, including 11 connection failures for Gemma. Completed responses were
retained. `--resume` checks task hashes, generation settings, model digests and
Ollama version; it archives connection failures before retrying them. Wrong model
answers are retained. No failed inference response is silently replaced with a
better sample. The endpoint was pinned to the SSH-confirmed LAN address
`192.168.188.170`; the report URL remains `http://minis:3001/`.

The evaluator was moved to the same pinned Docker image on minis via
`DOCKER_HOST=ssh://tom@192.168.188.170`, avoiding client Docker contention.
This changes evaluation location, not inference settings or saved response times.

Gemma's existing installation enables MTP speculative decoding with a draft
model (`draft_num_predict=3`). Ollama `/api/ps` reports 1.243 GiB, inconsistent with
server logs: the main model alone has 7024.34 MiB of GPU weights and the draft has
428.53 MiB. The sum is 7.278 GiB **for weights alone**, excluding KV, compute and
other buffers. This API memory value must not be used as actual footprint. The
report marks it unreliable and retains raw evidence. The installed Ollama source
was not present in the inspected wrapper repository; no runtime binary was patched.

To resume a matching interrupted run:

```bash
DOCKER_HOST=ssh://tom@192.168.188.170 .venv/bin/allama benchmark \
  --url http://192.168.188.170:11434 \
  --models gpt-oss:20b qwen3.5:9b gemma4:12b qwen3.8:27b devstral-small-2:24b \
  --repeats 2 --context 8192 --limit 1024 --unload-existing \
  --output benchmark-results --resume
```

### Concurrent inference

OpenWebUI submitted GPT-OSS and Gemma requests while the Qwen 27B group was running.
Four Qwen attempts were conservatively excluded from the performance comparison
and retained in `superseded_interference_attempts`. The user confirmed a quiet
window. That group was restarted; the runner now checks `/api/ps` before and after
every trial and stops on other resident models. Boundary checks cannot detect a
second request to the same model, so a quiet server remains necessary.

Regression coverage also checks reference implementations for every task,
resume compatibility, transport retries, infrastructure classification, early
process exit, timeout, no-network execution and HTML escaping. Mobile inspection
found an overflowing SHA256 string; wrapping was corrected.

### Installed profile differences

Common generation settings are context, token limit, temperature and seed. Other
model defaults remain in effect and are recorded in `models[].parameters`.
In particular, Qwen 9B advertises presence_penalty=1.5; Qwen 27B has
presence_penalty=0 and embedded MTP (`draft_num_predict=4`, confirmed in server
logs). Gemma has a separate draft model with three draft tokens. GPT-OSS and
Devstral do not declare a draft. This measures the installed profiles; the
per-model decoder settings are part of the configuration being compared.


## Delivery ledger

- Completed: 60 selected trials, reevaluation of all 60 answers, 48 passing
  regression tests, memory measurement and desktop/mobile browser verification.
- Locally committed: implementation through `2d3ad0d`; final evidence is included
  with this document on `ticket/001-minis-benchmark`.
- Pushed / PR-open: neither; the protected registry has no `wronai/allama` profile.
- Merged / deployed: source is not merged. The report is deployed on minis at
  `http://minis:3001/`, with enabled user service `allama-report`.

The report was opened in Chromium on minis and through the local default browser.
Browser readback: HTTP 200, five model rows, 60/60 attempts, no page errors, no
horizontal overflow at 390px width. [Screenshot](minis-20261008/report-final.png).
The user can resume normal model requests; timed inference is finished.
