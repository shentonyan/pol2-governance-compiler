# PoL2 Governance Compiler

[中文](README.md)

A knowledge-and-gates-only toolbox for [NaturalDAO PoL-Governance](https://github.com/naturaldao/NaturalDAO/tree/main/PoL-Governance). A coding agent uses it to compile a PoL2 runtime governance layer for one concrete host (for example a DSH plugin), while immutable gates stop it from passing the evaluation through shortcuts such as blocking everything or reading the test set.

The approach borrows from [MetaInfer](https://github.com/HuangPuStar/MetaInfer): MetaInfer generates a dedicated inference engine per (model × hardware × workload); this project compiles a dedicated governance layer per (host × decision surface × clause subset × latency budget).

> **Status: v0.1.0, phase 0 in progress.** Three of the ten gates exist (G02, G04, G06), plus three constant degenerate policies. No model is connected and there is **no claim about model quality**.

## What it does

PoL-Governance's SPEC and PROTOCOL already state the evaluation rules in prose: splits never cross a scenario family, the private holdout never enters the repository, thresholds come only from validation data, and blocking everything must not earn a good score through a low miss rate. This project turns those rules into scripts that any data, prediction file or result card has to pass before it enters the shared baseline.

| Layer | Directory | Role | Status |
|---|---|---|---|
| Knowledge | [contracts/](contracts/README.md), [rulings/](rulings/README.md) | Clause crosswalk; queue of clause ambiguities for team rulings | Crosswalk and open list exist; contract files are phase 1 |
| Gates | [gates/](gates/) | Immutable scripts that quote the SPEC sentence they enforce when they fail | G02, G04, G06 |
| Floor | [baselines/](baselines/README.md) | "Cheaters" that always run beside a candidate | Three constant policies |
| Roles | [skills/](skills/README.md) | SOPs for compiler, clause reviewer, blind evaluator | Drafts |
| Targets | [judges/](judges/README.md), [hosts/](hosts/README.md) | Pluggable judges; host requirement format | Not started |

## Quick start

Python 3.10+ only; no dependencies, no models.

```powershell
python -m unittest discover -s tests -t .
python -m baselines.constant --policy always_block --inputs data/pilot/pilot.jsonl --out build/always_block.jsonl
python -m gates.run_all --cases data/pilot/pilot.jsonl --predictions build/always_block.jsonl
```

The last command exits with code 1, as intended: on the 20 public pilot cases (9 violating, 9 normal, 2 insufficient) every constant policy sits on J = 1 − miss − over = 0, and G06 rules always_block "not above floor". A candidate must beat every random mixture of the degenerate policies on both error rates at once, which amounts to J > 0. Beating each policy separately is not enough; [docs/gate-design.md](docs/gate-design.md#g06-为什么是凸包而不是单点) explains why.

The pilot cases are assistant-written and unreviewed; they exercise the interface and must not be used for ranking.

## Honesty

Gates only block shortcuts someone has thought of; passing them does not show that a governance layer works. Nothing measured on the pilot is evidence of quality, and results on synthetic data do not generalise to real people. See [docs/honesty.md](docs/honesty.md).

## License

Original code and documentation: [CC0 1.0](LICENSE), matching PoL-Governance. Provenance of `data/pilot/`: [data/pilot/README.md](data/pilot/README.md).
