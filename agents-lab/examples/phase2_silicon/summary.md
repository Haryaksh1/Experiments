# Run `silicon`

- dir: `runs/20261016-002357_silicon`
- git: `6d01ad0-dirty`
- model: `phi3:mini`
- wall clock: 1053.8 s
- LLM calls: 140, attempts: 140, parse failure rate: 0.0%

## LLM calls by tag

| tag | calls | attempts | failed_attempts | final_failures | prompt_tokens | completion_tokens | latency_s | parse_fail_rate |
|---|---|---|---|---|---|---|---|---|
| survey | 140 | 140 | 0 | 0 | 43233 | 8156 | 1.05e+03 | 0 |

## Silicon sample

- Personas: 140, failed: 0

### PPI++ per item (n labeled, N simulated-only; truth = real answers of all n+N)

| item | n | N | truth_all_real | classical_real_n | naive_sim | ppi | ci_low | ci_high | ci_covers_truth | rho | lam | n_eff | agreement | majority_baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cappun | 40 | 100 | 0.6 | 0.6 | 0.114 | 0.606 | 0.456 | 0.756 | True | 0.272 | 0.287 | 42.2 | 0.5 | 0.6 |
| gunlaw | 40 | 100 | 0.629 | 0.55 | 0.886 | 0.542 | 0.393 | 0.691 | True | 0.369 | 0.395 | 44.3 | 0.65 | 0.55 |
| grass | 40 | 100 | 0.671 | 0.725 | 0.507 | 0.729 | 0.59 | 0.869 | True | -0.107 | -0.069 | 40.3 | 0.475 | 0.725 |
| natenvir | 40 | 100 | 2.59 | 2.48 | 2.3 | 2.47 | 2.23 | 2.71 | True | 0.037 | 0.023 | 40 | 0.45 | 0.65 |
| happy | 40 | 100 | 1.93 | 1.77 | 1.64 | 1.8 | 1.61 | 1.99 | True | -0.226 | -0.185 | 41.5 | 0.375 | 0.575 |

### Spread by party (sd_ratio < 1 = flattening)

| item | group | count | real_mean | sim_mean | real_sd | sim_sd | sd_ratio_sim_over_real |
|---|---|---|---|---|---|---|---|
| cappun | all | 140 | 0.6 | 0.114 | 0.492 | 0.319 | 0.649 |
| cappun | Democrat | 65 | 0.446 | 0.015 | 0.501 | 0.124 | 0.248 |
| cappun | Independent/other | 27 | 0.519 | 0 | 0.509 | 0 | 0 |
| cappun | Republican | 48 | 0.854 | 0.312 | 0.357 | 0.468 | 1.31 |
| gunlaw | all | 140 | 0.629 | 0.886 | 0.485 | 0.319 | 0.658 |
| gunlaw | Democrat | 65 | 0.831 | 0.985 | 0.378 | 0.124 | 0.328 |
| gunlaw | Independent/other | 27 | 0.556 | 1 | 0.506 | 0 | 0 |
| gunlaw | Republican | 48 | 0.396 | 0.688 | 0.494 | 0.468 | 0.948 |
| grass | all | 140 | 0.671 | 0.507 | 0.471 | 0.502 | 1.06 |
| grass | Democrat | 65 | 0.785 | 0.615 | 0.414 | 0.49 | 1.18 |
| grass | Independent/other | 27 | 0.704 | 0.519 | 0.465 | 0.509 | 1.09 |
| grass | Republican | 48 | 0.5 | 0.354 | 0.505 | 0.483 | 0.957 |
| natenvir | all | 140 | 2.59 | 2.3 | 0.709 | 0.837 | 1.18 |
| natenvir | Democrat | 65 | 2.91 | 2.37 | 0.292 | 0.802 | 2.75 |
| natenvir | Independent/other | 27 | 2.74 | 2.37 | 0.526 | 0.792 | 1.51 |
| natenvir | Republican | 48 | 2.08 | 2.17 | 0.895 | 0.907 | 1.01 |
| happy | all | 140 | 1.93 | 1.64 | 0.685 | 0.496 | 0.723 |
| happy | Democrat | 65 | 1.83 | 1.69 | 0.651 | 0.465 | 0.714 |
| happy | Independent/other | 27 | 1.89 | 1.67 | 0.698 | 0.48 | 0.688 |
| happy | Republican | 48 | 2.08 | 1.56 | 0.71 | 0.542 | 0.764 |
