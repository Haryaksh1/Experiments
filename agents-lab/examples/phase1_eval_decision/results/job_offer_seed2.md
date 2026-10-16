# Decision memo: Which job offer should a mid-career analyst accept?

**Recommendation: Bank** (margin 2.18 on a 0-10 scale)

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Bank | 7.55 | 5.8 | 9.1 |
| University | 5.37 | 3.4 | 7.2 |
| Startup | 5.2 | 3.4 | 7 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | salary | Bank | 8.83 | 1.56 | 7.28 | University |

Dominated on expected scores: Startup, University

## Clarification

Missing information:
- Expected salary increase at Startup
- Startup's industry growth rate
- Specific job roles and expectations in University position beyond seniority-based promotions
- University employment benefits package
Assumptions:
A1. The equity value of the Startup is expected to double within two years.
A2. Given industry trends, startups have a high growth potential which may align with career aspirations for rapid skill development and advancement in F3's sector.
A3. Additional benefits at University such as health care subsidies or retirement savings contributions are included beyond the seniority-based promotions mentioned
A4. The stability of employment is a critical factor, hence assuming that Bank offers better job security compared to Startup given its 10-year record

## Scores

| option | criterion | low | mid | high | basis | justification |
|---|---|---|---|---|---|---|
| Startup | salary | 4 | 6 | 8 | fact | High potential for rapid growth and responsibility. |
| Startup | growth | 4 | 6 | 8 | fact | High growth potential with equity and responsibility. |
| Startup | work_life | 3 | 5 | 7 | fact | Higher pay but long hours; equity potential and responsibility. |
| Startup | stability | 2 | 3 | 4 | fact | High risk due to uncertain funding and long hours. |
| Bank | salary | 7 | 9 | 10 | fact | Stable employment with structured promotions and higher salary. |
| Bank | growth | 5 | 7 | 9 | assumption | Stable with structured promotions and no layoffs. |
| Bank | work_life | 6 | 8 | 10 | fact | Stable job with good pay and structured growth. |
| Bank | stability | 5 | 6 | 7 | fact | Stable employment with structured promotions and no layoffs in a century. |
| University | salary | 3 | 5 | 7 | fact | Lower salary but stable role with seniority-based promotions. |
| University | growth | 3 | 5 | 7 | assumption | Slower growth but stable permanent role with benefits. |
| University | work_life | 4 | 7 | 9 | assumption | Best work-life balance with lower pay but seniority promotions. |
| University | stability | 4 | 5 | 6 | assumption | Permanent role with seniority-based promotions and likely benefits. |
