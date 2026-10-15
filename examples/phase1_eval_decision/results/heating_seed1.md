# Decision memo: Which heating system should a family install in their house?

**Recommendation: Heat pump** (margin 1.12 on a 0-10 scale)

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Heat pump | 7.8 | 6.6 | 9 |
| Gas boiler | 6.68 | 5.65 | 7.85 |
| Pellet stove | 5.2 | 4 | 6.4 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | running_cost | Heat pump | 8 | 4.28 | 3.72 | Gas boiler |
| score | running_cost | Gas boiler | 6 | 9.72 | 3.72 | Gas boiler |
| score | upfront_cost | Heat pump | 8 | 3.53 | 4.47 | Gas boiler |
| weight | reliability | (weights) | 0.2 | 0.59 | 0.39 | Gas boiler |

Dominated on expected scores: Pellet stove

## Clarification

Missing information:
- Comparative emissions between heat pump when using renewable energy sources vs natural gas.
- Expected future prices of electricity and gas in the family's area over the next decade.
- Local availability and reliability of pellet supply for refilling the stove on a regular basis.
- Number of expected servicing breakdowns per year specific to each heating system installed.
Assumptions:
A1. The family's house is in an area with consistent electricity pricing, reducing uncertainty related to future energy costs for the heat pump and boiler.
A2. Pellet supply chains are expected to stabilize due to increased domestic demand or government subsidies aimed at renewable resources.
A3. The reliability of local installers is assumed consistent across all three heating systems, reducing risk in equipment servicing and repairs.
A4. Future legislation towards carbon taxes will increase the cost-effectiveness of low emissions options like heat pumps.

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Heat pump | upfront_cost | 7 | 8 | 9 | fact | After grant reduces upfront cost; emissions are higher than desired. |
| Heat pump | running_cost | 7 | 8 | 9 | fact | Low running cost and CO2 emissions; requires specialist service. |
| Heat pump | emissions | 7 | 8 | 9 | fact | Low emissions but requires specialist servicing. |
| Heat pump | reliability | 5 | 7 | 9 | fact | Specialist servicing needed; local installers available. |
| Gas boiler | upfront_cost | 6 | 7 | 8 | fact | Lower upfront cost and emissions compared to heat pump. |
| Gas boiler | running_cost | 5 | 6 | 7 | fact | Cheaper running cost but higher CO2 emissions. |
| Gas boiler | emissions | 5 | 6 | 7 | fact | Higher emissions and running costs. |
| Gas boiler | reliability | 7 | 8 | 10 | fact | Many local technicians; lower servicing needs. |
| Pellet stove | upfront_cost | 4 | 5 | 6 | fact | Higher upfront cost and manual refilling inconvenience. |
| Pellet stove | running_cost | 4 | 5 | 6 | fact | Higher running cost and manual refilling; supply disruption risk. |
| Pellet stove | emissions | 4 | 5 | 6 | fact | Lower emissions but manual refilling and supply uncertainty. |
| Pellet stove | reliability | 4 | 6 | 8 | fact | Weekly refilling; past supply disruption. |
