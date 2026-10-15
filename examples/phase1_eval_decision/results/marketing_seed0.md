# Decision memo: Which channel should a B2B software company spend its $50,000 lead-generation budget on?

**Recommendation: Search ads** (margin 0.55 on a 0-10 scale; model confidence: high)

Given our goal of cost-effective and timely lead generation within a B2B sector, we recommend Search ads as they offer an optimal balance in terms of lower costs per lead (F1), reasonable speed for results arrival well before the quarter's end (F1), full measurability with comprehensive tracking capabilities (F1), while maintaining quality through targeted search advertising which is crucial to our niche B2B market. The highest expected weight score of 7.25 indicates Search ads are most aligned,

## Key risks
- Search Ad prices may rise unexpectedly in the next quarter (uncertainty).

## Evidence that would change the decision
- Trade show leads are more effective with personalized interactions, or if historical data shows higher lead quality from Trade Shows.
- Influencer audience demographics fully match target B2B sector needs and provide valuable insights that could enhance the effectiveness of Influencers as a go-a

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Search ads | 7.25 | 5.8 | 8.7 |
| Trade shows | 6.7 | 5.3 | 7.9 |
| Influencers | 4.62 | 2.8 | 6.15 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | cost_per_lead | Search ads | 8 | 6.62 | 1.37 | Trade shows |
| score | cost_per_lead | Trade shows | 6 | 7.38 | 1.37 | Trade shows |
| score | lead_quality | Search ads | 6 | 4.17 | 1.83 | Trade shows |
| weight | lead_quality | (weights) | 0.3 | 0.41 | 0.11 | Trade shows |
| weight | cost_per_lead | (weights) | 0.4 | 0.17 | 0.23 | Trade shows |

Dominated on expected scores: Influencers

## Clarification

Missing information:
- Historical lead conversion rates from trade shows
- Influencer audience demographics match target B2B sector needs
Assumptions:
A1. Search ad prices remain stable or increase in the next quarter, making now a better time to invest.
A2. Trade show leads will be as effective if not more because of personalized interactions during events.
A3. Influencer audience demographics partially overlap with B2B sector needs, providing valuable insights for follow-up actions.
A4. Quality over quantity is prioritized; therefore, only the highest potential clients from each channel will be pursued further.

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Search ads | cost_per_lead | 7 | 8 | 9 | fact | Low cost per lead; immediate results. |
| Search ads | lead_quality | 4 | 6 | 8 | fact | 25% qualified leads with full tracking. |
| Search ads | speed | 6 | 7 | 8 | fact | Results arrive within 2 weeks; fast and trackable. |
| Search ads | measurability | 6 | 8 | 10 | fact | Every lead is fully tracked; precise measurement possible. |
| Trade shows | cost_per_lead | 5 | 6 | 7 | assumption | Higher lead quality; personalized interaction. |
| Trade shows | lead_quality | 7 | 9 | 10 | assumption | 40% qualified leads with personalized interactions. |
| Trade shows | speed | 4 | 5 | 6 | assumption | Results in less than a month; personalized interactions. |
| Trade shows | measurability | 4 | 6 | 8 | fact | Lead tracking uses badge scans; less precise but still measurable. |
| Influencers | cost_per_lead | 4 | 5 | 6 | assumption | Mid-range cost; some audience overlap. |
| Influencers | lead_quality | 2 | 5 | 7 | assumption | 8% qualified leads with partial audience overlap. |
| Influencers | speed | 2 | 4 | 5 | assumption | Results in less than a month; demographic insights. |
| Influencers | measurability | 2 | 4 | 6 | assumption | Tracking uses promo codes only; less precise measurement. |
