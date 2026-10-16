# Decision memo: Which venue should host a 400-person industry conference?

**Recommendation: Hotel Central** (margin 1.04 on a 0-10 scale; model confidence: high)

Recommended venue for a 400-person industry conference is Hotel Central, as it meets all critical criteria effectively. While slightly above budget at $60k vs $70k limit ($10k catering), its close capacity fit and superior amenities (F1) outweigh the cost difference when considering factors such as expected attendance fluctuation and potential for increased networking with on-site catering. Prioritizing a professional atmosphere, our decision leans towards Hotel Central due to F3.

## Key risks
- Final cost may exceed initial estimates

## Evidence that would change the decision
- If final attendance significantly surpasses 420, leading to additional charges or venue unavailability.
- Should COVID-19 regulations change in the future impacting gatherings size and safety measures cost implications on Hotel Central's pricing structure.
- Increased demand for catered services at Expo Hall could raise costs, surpassing Hotel Central.

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Hotel Central | 7.75 | 6.75 | 8.75 |
| Expo Hall | 6.71 | 5.5 | 7.75 |
| University Campus | 6 | 5 | 7 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | cost | Hotel Central | 8 | 4.53 | 3.47 | Expo Hall |
| score | capacity_fit | Hotel Central | 8 | 3.83 | 4.17 | Expo Hall |
| score | accessibility | Hotel Central | 7 | 2.83 | 4.17 | Expo Hall |

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
| Hotel Central | cost | 7 | 8 | 9 | fact | Fits capacity and includes amenities; cost within budget with COVID-19 adjustments. |
| Hotel Central | capacity_fit | 7 | 8 | 9 | fact | Fits capacity well with extra space for attendees. |
| Hotel Central | accessibility | 6 | 7 | 8 | fact | 5-minute walk to station; central location. |
| Hotel Central | amenities | 7 | 8 | 9 | fact | Includes catering and AV; cost-effective within budget. |
| Expo Hall | cost | 6 | 7 | 8 | assumption | Cheaper overall; good accessibility and AV setup. |
| Expo Hall | capacity_fit | 6 | 7 | 8 | assumption | Large capacity with potential for AV setup and high-quality catering. |
| Expo Hall | accessibility | 4 | 6 | 7 | assumption | Shuttle service available; larger venue. |
| Expo Hall | amenities | 6 | 7 | 8 | assumption | High-quality AV and catering; cost within budget after shuttle. |
| University Campus | cost | 5 | 6 | 7 | assumption | Most cost-effective; close to capacity and within walking distance. |
| University Campus | capacity_fit | 5 | 6 | 7 | assumption | Close capacity fit with added convenience of walking to station. |
| University Campus | accessibility | 5 | 6 | 7 | assumption | 10-minute walk; good capacity and amenities. |
| University Campus | amenities | 5 | 6 | 7 | assumption | Close capacity fit; basic AV and student union catering. |
