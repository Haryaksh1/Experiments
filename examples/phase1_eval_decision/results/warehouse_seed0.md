# Decision memo: Where should a distributor open its new warehouse?

**Recommendation: Eastgate** (margin 0.67 on a 0-10 scale; model confidence: medium)

Based on lower rent ($7/sqft) and reasonable customer proximity, Eastgate scores highest with a weighted score of 7.48; accessibility improvements bolster confidence in Northfield.

## Key risks
- Potential delays due to environmental impact assessments for expansion

## Evidence that would change the decision
- Northfield develops a key industry hub, increasing customer growth rates significantly over Riverside and Eastgate.
- A major transportation project improves accessibility in Northfield dramatically
- Rent prices drop disproportionately in Eastgate due to an oversupply of warehouses.

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Eastgate | 7.48 | 6.2 | 9.05 |
| Northfield | 6.8 | 5.15 | 8.45 |
| Riverside | 4.35 | 2.7 | 6 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | proximity | Eastgate | 8 | 6.07 | 1.93 | Northfield |
| score | proximity | Northfield | 7 | 8.93 | 1.93 | Northfield |
| score | rent | Eastgate | 8.17 | 5.92 | 2.25 | Northfield |
| weight | labor | (weights) | 0.2 | 0.52 | 0.32 | Northfield |

Dominated on expected scores: Riverside

## Clarification

Missing information:
- Transportation accessibility in Northfield
- Projected customer growth rates at all locations
- Average wage differences for hiring labor between cities
- Local regulations regarding expansion and land use
Assumptions:
A1. Northfield's transportation accessibility will not significantly decrease due to renting adjacent free land.
A2. Customer growth rates are expected to remain stable across the three locations within a 5% range per year.
A3. Wage differences between Northfield and Riverside do not exceed $2, with Eastgate being comparable in this regard.
A4. Local regulations allow for warehouse expansion but require environmental impact assessments.

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Northfield | rent | 5 | 7 | 9 | fact | Cheaper rent and good customer proximity; potential for expansion. |
| Northfield | proximity | 6 | 7 | 8 | fact | High customer proximity but concerns over transportation accessibility. |
| Northfield | labor | 4 | 6 | 8 | fact | Lower unemployment and free land for expansion. |
| Northfield | expansion | 5 | 7 | 9 | fact | Good rent and land availability for expansion. |
| Riverside | rent | 2 | 4 | 6 | fact | Highest rent; no local land for expansion. |
| Riverside | proximity | 4 | 5 | 6 | fact | Lower customer proximity but higher rent. |
| Riverside | labor | 2 | 4 | 6 | fact | Higher rent and no local resources for expansion. |
| Riverside | expansion | 2 | 4 | 6 | fact | High rent and no land or schools. |
| Eastgate | rent | 7 | 8 | 10 | fact | Cheapest rent; good customer proximity and labor availability. |
| Eastgate | proximity | 7 | 8 | 9 | fact | Best proximity and favorable labor conditions. |
| Eastgate | labor | 3 | 5 | 7 | fact | Lower rent and one logistics school. |
| Eastgate | expansion | 7 | 8 | 10 | fact | Best rent and land availability for expansion. |
