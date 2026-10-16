# Decision memo: Which job offer should a mid-career analyst accept?

**Recommendation: Bank** (margin 0.32 on a 0-10 scale)

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Bank | 7.2 | 5.7 | 8.7 |
| University | 6.88 | 5 | 8.3 |
| Startup | 5.45 | 3.9 | 7.2 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | salary | Bank | 8 | 6.94 | 1.06 | University |
| score | salary | University | 6.83 | 7.89 | 1.06 | University |
| score | growth | Bank | 6 | 4.94 | 1.06 | University |
| weight | work_life | (weights) | 0.2 | 0.28 | 0.08 | University |
| weight | salary | (weights) | 0.3 | 0.04 | 0.26 | University |
| weight | growth | (weights) | 0.3 | 0.72 | 0.42 | Startup |

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
| Startup | salary | 3 | 5 | 7 | fact | High salary with equity potential but long hours and uncertain funding. |
| Startup | growth | 6 | 7 | 9 | fact | High growth potential with equity and responsibility. |
| Startup | work_life | 3 | 4 | 5 | fact | Higher pay but with longer hours and equity uncertainty. |
| Startup | stability | 3 | 5 | 7 | fact | High risk due to uncertain funding and long hours. |
| Bank | salary | 6 | 8 | 10 | fact | Stable job with structured promotions and highest salary. |
| Bank | growth | 5 | 6 | 7 | assumption | Stable with structured promotions and no layoffs. |
| Bank | work_life | 6 | 7 | 8 | fact | Stable job with good pay and structured growth. |
| Bank | stability | 6 | 8 | 10 | fact | Stable employment with structured promotions and no layoffs in a century. |
| University | salary | 4 | 7 | 9 | fact | Lower salary but stable role with potential benefits and seniority-based promotions. |
| University | growth | 4 | 5 | 6 | assumption | Slower growth but permanent staff role with benefits. |
| University | work_life | 9 | 10 | 10 | assumption | Best work-life balance with steady pay and benefits. |
| University | stability | 4 | 7 | 9 | assumption | Stable permanent role with potential benefits. |
