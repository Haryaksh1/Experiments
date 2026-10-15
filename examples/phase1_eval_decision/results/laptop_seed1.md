# Decision memo: Which laptop should a university student buy for the next three years?

**Recommendation: Core 13** (margin 1.54 on a 0-10 scale)

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Core 13 | 8.89 | 7.95 | 9.6 |
| Aero 14 | 7.35 | 6.1 | 8.6 |
| Bolt 15 | 6.13 | 4.55 | 7.45 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | cost | Core 13 | 9.83 | 5.43 | 4.4 | Aero 14 |
| score | battery | Core 13 | 8 | 1.83 | 6.17 | Aero 14 |
| score | performance | Core 13 | 9 | 2.83 | 6.17 | Aero 14 |

Dominated on expected scores: Aero 14, Bolt 15

## Clarification

Missing information:
- Keyboard comfort level
- Battery life under heavy usage (e.g., video editing)
- Cross-platform compatibility for software used in university courses
- Availability of the laptop models within budget
Assumptions:
A1. - Keyboard comfort level does not significantly differ between laptops.
A2. - Battery life under heavy usage is similar to battery performance provided ($700, $950, and $650 options).
A3. - Cross-platform compatibility for software used in university courses exists across all laptop brands (Aero 14, Bolt 15, Core 13).
A4. The student has a preference to stay within the budget of at most $1,000.

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Aero 14 | cost | 7 | 8 | 9 | fact | Best cost-to-performance ratio with acceptable battery life. |
| Aero 14 | battery | 5 | 7 | 9 | fact | Longest battery life within budget. |
| Aero 14 | performance | 6 | 7 | 8 | fact | Good balance of cost and performance. |
| Aero 14 | portability | 6 | 7 | 8 | fact | Lightest and most portable option within budget. |
| Bolt 15 | cost | 6 | 7 | 8 | fact | Higher performance but at a higher cost and heavier weight. |
| Bolt 15 | battery | 3 | 6 | 8 | fact | Mid-range battery life and performance. |
| Bolt 15 | performance | 5 | 6 | 7 | fact | Best performance but higher cost. |
| Bolt 15 | portability | 3 | 5 | 6 | fact | Heavier and less portable than Aero. |
| Core 13 | cost | 9 | 10 | 10 | assumption | Best performance and battery life within budget. |
| Core 13 | battery | 7 | 8 | 9 | fact | Best battery life and performance. |
| Core 13 | performance | 8 | 9 | 10 | assumption | Best performance and cost. |
| Core 13 | portability | 7 | 8 | 9 | fact | Lightest and most portable option with best performance. |
