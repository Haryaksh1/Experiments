# Decision memo: Which venue should host a 400-person industry conference?

**Recommendation: Hotel Central** (margin 1.24 on a 0-10 scale)

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Hotel Central | 7.95 | 6.95 | 8.95 |
| Expo Hall | 6.71 | 5.5 | 7.75 |
| University Campus | 6 | 5 | 7 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | cost | Hotel Central | 8 | 3.86 | 4.14 | Expo Hall |
| score | capacity_fit | Hotel Central | 8 | 3.03 | 4.97 | Expo Hall |
| score | accessibility | Hotel Central | 7 | 2.03 | 4.97 | Expo Hall |

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
| Hotel Central | cost | 7 | 8 | 9 | fact | Fits capacity and includes amenities; cost within budget with COVID-19 adjustment. |
| Hotel Central | capacity_fit | 7 | 8 | 9 | fact | Close to capacity; good accessibility and amenities. |
| Hotel Central | accessibility | 6 | 7 | 8 | fact | 5-minute walk to station; central location. |
| Hotel Central | amenities | 8 | 9 | 10 | fact | Includes catering and AV; fits capacity well. |
| Expo Hall | cost | 6 | 7 | 8 | assumption | Cheaper overall cost with high capacity and AV flexibility. |
| Expo Hall | capacity_fit | 6 | 7 | 8 | fact | Lower cost with good capacity and amenities; accessible by shuttle. |
| Expo Hall | accessibility | 4 | 6 | 7 | assumption | Shuttle service available; larger venue. |
| Expo Hall | amenities | 6 | 7 | 8 | assumption | High-quality AV and catering; larger capacity. |
| University Campus | cost | 5 | 6 | 7 | fact | Most cost-effective option with good capacity and proximity to station; catering extra. |
| University Campus | capacity_fit | 5 | 6 | 7 | assumption | Best capacity fit; accessible and includes basic AV with potential for quality catering. |
| University Campus | accessibility | 5 | 6 | 7 | assumption | 10-minute walk; good capacity and amenities. |
| University Campus | amenities | 5 | 6 | 7 | assumption | Close capacity; basic AV with potential extra cost. |
