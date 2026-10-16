# Decision memo: Which supplier should a manufacturer choose for a key component?

**Recommendation: Supplier A** (margin 2.00 on a 0-10 scale; model confidence: high)

Supplier A is chosen for its balance of cost-efficiency and reliability. With a unit_cost score of 7.70, it outperforms Suppliers B (5.70) and C (2.97), while maintaining the lowest defect rate at only 0.5% with no associated rework costs mentioned in the facts.

## Key risks
- Uncertainty regarding Supplier A's ability to handle future demand fluctuations.

## Evidence that would change the decision
- If Supplier B can match or reduce their defect rate and lead time closer to Supplier A, they could become more competitive.
- Supplier C managing a significant reduction in both their defect rate and improving delivery times within the next year would make them viable again.

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Supplier A | 7.7 | 6.6 | 8.8 |
| Supplier B | 5.7 | 4.6 | 6.8 |
| Supplier C | 2.97 | 1.8 | 4.4 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | unit_cost | Supplier A | 8 | 3 | 5 | Supplier B |
| score | defect_rate | Supplier A | 8 | 1.33 | 6.67 | Supplier B |

Dominated on expected scores: Supplier B, Supplier C

## Clarification

Missing information:
- Exact cost difference between Supplier A's defect rate rework costs and their base unit price compared to other suppliers.
- Supplier C's potential for reducing its lead time within the next year, if applicable or possible.
- Information on how flexible each supplier is regarding quantity adjustments based on demand fluctuations (if any).
- Existing relationships with these suppliers and their impact on negotiation power.
Assumptions:
A1. Assuming Supplier C will not be able to significantly reduce its defect rate within the next year, they should likely be eliminated from consideration based on-

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Supplier A | unit_cost | 7 | 8 | 9 | fact | Lowest unit cost and acceptable defect rate. |
| Supplier A | defect_rate | 7 | 8 | 9 | fact | Lowest defect rate and reasonable lead time. |
| Supplier A | lead_time | 7 | 8 | 9 | fact | Shortest lead time with acceptable defect rate and cost. |
| Supplier A | capacity | 3 | 5 | 7 | fact | Limited capacity but best unit cost and lead time. |
| Supplier B | unit_cost | 5 | 6 | 7 | fact | Higher unit cost and defect rate than Supplier A. |
| Supplier B | defect_rate | 5 | 6 | 7 | fact | Higher defect rate and longer lead time. |
| Supplier B | lead_time | 5 | 6 | 7 | fact | Longer lead time and higher defect rate than Supplier A. |
| Supplier B | capacity | 1 | 3 | 5 | fact | Higher defect rate and lead time than A. |
| Supplier C | unit_cost | 2 | 3 | 5 | assumption | Lowest unit cost but highest defect rate and lead time. |
| Supplier C | defect_rate | 2 | 3 | 4 | fact | Highest defect rate and longest lead time. |
| Supplier C | lead_time | 2 | 3 | 4 | fact | Longest lead time and highest defect rate. |
| Supplier C | capacity | 0 | 2 | 4 | assumption | Highest capacity but worst lead time and defect rate. |
