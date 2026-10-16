# Decision memo: Which job offer should a mid-career analyst accept?

**Recommendation: Bank** (margin 1.47 on a 0-10 scale; model confidence: high)

The Bank offer aligns best with our criteria: it provides a higher salary ($95,000 vs. $65,000-70k), has clear growth opportunities (structured promotion track every two years) and offers stability given its 10-year record of no layoffs in the analyst's department; University is ranked second due to lower salary despite good work conditions.

## Key risks
- Risk associated with a possible industry downturn affecting job stability.

## Evidence that would change the decision
- If the expected salary increase at Startup was higher than 10%, e.g., $85,000 after two years
- University offering a competitive package with immediate promotion potential and high-impact projects
- Bank's sector facing uncertainty that might affect its regular review cycle for promotions

## Ranking (computed in Python)

| option | expected | low | high |
|---|---|---|---|
| Bank | 8.3 | 6.6 | 9.6 |
| University | 6.83 | 4.7 | 8.3 |
| Startup | 6 | 4.2 | 7.8 |

## Sensitivity: smallest single changes that flip the top choice

| change | criterion | option | before | after | size | overtaker |
|---|---|---|---|---|---|---|
| score | salary | Bank | 8.83 | 3.94 | 4.89 | University |
| score | salary | University | 5 | 9.89 | 4.89 | University |
| score | growth | Bank | 8.83 | 3.94 | 4.89 | University |
| weight | stability | (weights) | 0.2 | 0.47 | 0.27 | University |

Dominated on expected scores: Startup

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
| Startup | growth | 6 | 8 | 10 | fact | High growth potential with equity and responsibility. |
| Startup | work_life | 3 | 5 | 7 | fact | Higher pay but long hours; equity potential and responsibility. |
| Startup | stability | 3 | 4 | 5 | fact | High risk due to uncertain funding and long hours. |
| Bank | salary | 7 | 9 | 10 | fact | Stable employment with structured promotions and higher salary. |
| Bank | growth | 7 | 9 | 10 | assumption | Stable with structured promotions and no layoffs. |
| Bank | work_life | 6 | 8 | 10 | fact | Stable job with good pay and structured growth. |
| Bank | stability | 6 | 7 | 8 | fact | Lower risk with structured promotions and no layoffs in a century. |
| University | salary | 3 | 5 | 7 | assumption | Lower salary but stable role with potential benefits. |
| University | growth | 4 | 7 | 8 | assumption | Slower growth but stable permanent role. |
| University | work_life | 4 | 7 | 9 | fact | Best work-life balance with steady pay and seniority promotions. |
| University | stability | 9 | 10 | 10 | assumption | Best stability with permanent role and seniority-based promotions. |
