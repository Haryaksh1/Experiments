# Decision memo: Which venue should host a 400-person industry conference?

**Recommendation: Hotel Central** (margin 1.00 on a 0-10 scale)

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Hotel Central | 7.7 | 6.7 | 8.7 |
| Expo Hall | 6.7 | 5.7 | 7.7 |
| University Campus | 6 | 5 | 7 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | cost | Hotel Central | 7 | 3.67 | 3.33 | Expo Hall |
| score | cost | Expo Hall | 6 | 9.33 | 3.33 | Expo Hall |
| score | capacity_fit | Hotel Central | 8 | 4 | 4 | Expo Hall |

Dominated on expected scores: Expo Hall, University Campus

## Clarification

Missing information:
- Current COVID-19 regulations regarding gatherings
- Specific seating arrangements or required setup for AV needs at Expo Hall and University Campus
- Quality of catering services provided by the student union versus external providers
Assumptions:
A1. COVID-19 regulations allow gatherings up to 500 people with safety measures in place, reducing Hotel Central's cost constraint
A2. Expo Hall can accommodate setup for AV requirements without additional costs due to its large size and flexible environment
A3. Catering services at Expo Hall are of high quality as it caters exclusively to events regularly but could be less personalized than student union offerings, imp
A4. assumptions_continuation truncated: assuming the industry conference's catered food is a priority due to its formality and networking aspect

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Hotel Central | cost | 6 | 7 | 8 | fact | Fits capacity and includes amenities; cost within budget with COVID-19 adjustments. |
| Hotel Central | capacity_fit | 7 | 8 | 9 | fact | Exceeds capacity needs and offers convenience with proximity to transport. |
| Hotel Central | accessibility | 7 | 8 | 9 | fact | 5-minute walk from station; central location. |
| Hotel Central | amenities | 7 | 8 | 9 | fact | Includes catering and AV; cost-effective within budget. |
| Expo Hall | cost | 5 | 6 | 7 | assumption | Cheaper overall cost with high capacity and AV flexibility. |
| Expo Hall | capacity_fit | 6 | 7 | 8 | assumption | Large capacity and AV flexibility; potential for high-quality catering. |
| Expo Hall | accessibility | 6 | 7 | 8 | assumption | 10-minute shuttle ride; large space. |
| Expo Hall | amenities | 6 | 7 | 8 | assumption | High-quality AV and catering; cost within budget after shuttle. |
| University Campus | cost | 5 | 6 | 7 | assumption | Most cost-effective; within budget and close to capacity. |
| University Campus | capacity_fit | 5 | 6 | 7 | assumption | Close to capacity; walkable access and student union catering. |
| University Campus | accessibility | 5 | 6 | 7 | assumption | 10-minute walk; basic AV and student union catering. |
| University Campus | amenities | 5 | 6 | 7 | assumption | Close capacity fit and convenient access; additional catering cost. |
