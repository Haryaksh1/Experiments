# Decision memo: Which web framework should a six-person team use for a new internal tool?

**Recommendation: Django** (margin 0.12 on a 0-10 scale; model confidence: high)

Given our team's Python proficiency and Django’s robust ecosystem, we recommend using Django for its ready-to-use admin features. With a score of 7.77 (Fact F3), it suits the majority skill set while offering required functionalities.

## Key risks
- team's ability to learn new frameworks quickly if needed

## Evidence that would change the decision
- If Express’ performance is critical for shipping within 3 months, its edge over Django would be significant.
- Increased familiarity with Ruby among team members might make Rails more approachable and could raise confidence in a switch to it.

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Django | 7.77 | 6.35 | 8.85 |
| Express | 7.65 | 6.65 | 8.65 |
| Rails | 7.24 | 5.95 | 8.3 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | team_familiarity | Django | 8 | 7.67 | 0.33 | Express |
| score | team_familiarity | Express | 7 | 7.33 | 0.33 | Express |
| score | ecosystem | Django | 7.83 | 7.37 | 0.47 | Express |
| weight | team_familiarity | (weights) | 0.35 | 0.26 | 0.09 | Express |
| weight | performance | (weights) | 0.15 | 0.24 | 0.09 | Express |
| weight | ecosystem | (weights) | 0.25 | 0.56 | 0.31 | Express |

Dominated on expected scores: Rails

## Clarification

Missing information:
- Current level of experience with Django among team members.
- Expected tool complexity based on functionality required from its admin panel or plugin-based authentication system.
Assumptions:
A1. Given the majority Python knowledge, Rails might be less familiar but manageable for all to learn quickly due to similarity with Ruby's syntax.
A2. If performance remains critical and under moderate load is expected, Express would suffice given its high speed benchmark; otherwise Django or Rails could fit.

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Django | team_familiarity | 7 | 8 | 9 | fact | Familiarity with Python and Django's built-in features align well. |
| Django | performance | 6 | 7 | 8 | fact | Familiarity and built-in features outweigh Express' speed. |
| Django | ecosystem | 6 | 8 | 9 | fact | Familiarity and robust ecosystem with maintained packages. |
| Django | hiring | 6 | 8 | 9 | fact | Familiarity and performance are Django's strengths; built-in admin panel is a plus. |
| Express | team_familiarity | 6 | 7 | 8 | fact | JavaScript knowledge is beneficial for Express' performance. |
| Express | performance | 7 | 8 | 9 | fact | Best performance among options. |
| Express | ecosystem | 7 | 8 | 9 | fact | High performance with a JavaScript-based ecosystem. |
| Express | hiring | 7 | 8 | 9 | fact | High performance and team's JavaScript knowledge favor Express. |
| Rails | team_familiarity | 4 | 6 | 7 | assumption | Familiarity with Ruby and Rails' similar syntax. |
| Rails | performance | 7 | 8 | 9 | assumption | Familiarity and performance are key; admin issues manageable. |
| Rails | ecosystem | 7 | 8 | 9 | fact | Familiarity with Ruby and a good ecosystem despite admin issues. |
| Rails | hiring | 7 | 8 | 9 | fact | Familiarity and local applicant pool are Rails' advantages. |
