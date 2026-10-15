# Decision memo: Which heating system should a family install in their house?

**Recommendation: Heat pump** (margin 0.65 on a 0-10 scale; model confidence: medium)

Recommend a heat pump due to its balance of upfront cost, running costs, and emissions. It offers lower installation expense after grant aid, moderate annual operating fees (F1), low CO2 output per year (F2) despite specialist servicing requirements.

## Key risks
- Specialized service technicians may be needed more frequently than expected.

## Evidence that would change the decision
- If local heat pump services become less reliable or face long wait times, consider the gas boiler instead.
- .
- Should CO2 emission costs significantly rise due to carbon taxation making low-emission options prohibit0ively expensive (F4), reassessing energy source suitabl

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Heat pump | 7.6 | 6.4 | 8.8 |
| Gas boiler | 6.95 | 5.95 | 7.95 |
| Pellet stove | 5 | 3.8 | 6.2 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | running_cost | Heat pump | 8 | 5.83 | 2.17 | Gas boiler |
| score | running_cost | Gas boiler | 7 | 9.17 | 2.17 | Gas boiler |
| score | upfront_cost | Heat pump | 8 | 5.4 | 2.6 | Gas boiler |
| weight | reliability | (weights) | 0.2 | 0.4 | 0.2 | Gas boiler |

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
| Heat pump | upfront_cost | 7 | 8 | 9 | fact | After grant reduces cost; emissions and servicing concerns exist. |
| Heat pump | running_cost | 7 | 8 | 9 | fact | Low running cost but higher emissions and specialist servicing needed. |
| Heat pump | emissions | 7 | 8 | 9 | fact | Low emissions but needs specialist servicing. |
| Heat pump | reliability | 4 | 6 | 8 | fact | Specialist servicing needed; local installers available. |
| Gas boiler | upfront_cost | 6 | 7 | 8 | fact | Cheaper upfront cost; higher emissions and servicing costs. |
| Gas boiler | running_cost | 6 | 7 | 8 | fact | Cheapest running cost but highest emissions and no specialist servicing needed. |
| Gas boiler | emissions | 5 | 6 | 7 | fact | Higher emissions and running costs. |
| Gas boiler | reliability | 7 | 8 | 9 | fact | Many local technicians; lower CO2 emissions than heat pump. |
| Pellet stove | upfront_cost | 4 | 5 | 6 | fact | Higher cost and manual refilling; supply concerns exist. |
| Pellet stove | running_cost | 4 | 5 | 6 | fact | Moderate running cost but requires manual refilling and had supply issues. |
| Pellet stove | emissions | 4 | 5 | 6 | assumption | Lower emissions but manual refilling and supply uncertainty. |
| Pellet stove | reliability | 3 | 5 | 7 | fact | Weekly refilling; past supply disruption. |
