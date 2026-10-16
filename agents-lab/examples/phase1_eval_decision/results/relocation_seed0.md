# Decision memo: Which city should a software engineer relocate to?

**Recommendation: Lisbon** (margin 1.03 on a 0-10 scale; model confidence: medium)

Lisbon is recommended due to its favorable cost of living and job market for software engineers, as well as better climate with more sunshine hours. Fact F1 suggests lower rent (F2 fact), while factoring in visa processing times aligns Lisbon best within the 6-month constraint set by Constraint C3.

## Key risks
- Dependence on securing a job offer, as per Uncertainty F1.

## Evidence that would change the decision
- If Toronto's housing costs decrease significantly making it comparable to Lisbon in affordability.
- Lisbon visa processing time becomes longer than expected delaying relocation within the 6-month window, tipping balance towards Berlin or Toronto based on their
- Berlin offers better job opportunities for engineers with specialized skills that command higher salaries adjusted by PPP in comparison to Lisbon.

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Lisbon | 7.8 | 6.8 | 8.8 |
| Berlin | 6.77 | 5.6 | 7.8 |
| Toronto | 6.42 | 5 | 7.5 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | cost_of_living | Lisbon | 8 | 4.56 | 3.44 | Berlin |
| score | job_market | Lisbon | 8 | 4.56 | 3.44 | Berlin |
| score | climate | Lisbon | 8 | 2.83 | 5.17 | Berlin |

Dominated on expected scores: Berlin, Toronto

## Clarification

Missing information:
- Current cost-of-living index comparison between Lisbon, Berlin, and Toronto.
- Average salary range for software engineers in all three cities adjusted for purchasing power parity (PPP).
- Availability of housing options suitable for a family considering the engineer's spouse or partner if applicable.
- Social benefits available to expatriates such as healthcare, education services, and community support.
Assumptions:
A1. The cost-of-living index will not change dramatically within a six-month period for any of the cities mentioned.
A2. A software engineer in these three locations has similar skills but with no significant differences in experience levels that would skew job market comparisons.
A3. Lisbon's climate is consistently warmer throughout the year, providing more sunshine compared to Berlin and Toronto evenly across seasons.
A4. An Express Entry visa for Canada offers a comprehensive pathway allowing skilled workers like software engineers from Europe to apply with ease.

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Lisbon | cost_of_living | 7 | 8 | 9 | fact | Lower rent and faster visa process. |
| Lisbon | job_market | 7 | 8 | 9 | fact | More software jobs and faster visa process. |
| Lisbon | climate | 7 | 8 | 9 | fact | Best climate with most sunshine and fast visa process. |
| Lisbon | visa_ease | 6 | 7 | 8 | fact | Fastest visa process for remote work. |
| Berlin | cost_of_living | 6 | 7 | 8 | fact | Moderate rent and EU visa speed. |
| Berlin | job_market | 6 | 7 | 8 | fact | More software jobs than Lisbon. |
| Berlin | climate | 5 | 7 | 8 | fact | Moderate sunshine and strong job market. |
| Berlin | visa_ease | 5 | 6 | 7 | fact | Quick EU Blue Card issuance with job offer. |
| Toronto | cost_of_living | 4 | 6 | 7 | fact | Higher rent but best climate and job market. |
| Toronto | job_market | 6 | 7 | 8 | fact | Most software jobs and potential for permanent residence. |
| Toronto | climate | 6 | 7 | 8 | fact | More sunshine than Berlin and a large job market. |
| Toronto | visa_ease | 4 | 6 | 7 | assumption | Express Entry pathway for skilled workers. |
