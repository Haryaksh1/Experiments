# Panel decision: Where should a distributor open its new warehouse?

**Recommendation: Northfield** (margin 0.90; agents isolated (ablation D))

## Step 1: brief

Framer's brief:
- Northfield: Lowest rent at $9/sqft; high customer proximity (70% within 2 hrs); reasonable labor market and expansion potential. [facts: F1, F2]
- Riverside: Higher rent ($12/sqft), moderate customer reach, low unemployment but no local logistics training or expandable land. [facts: F3, F4]
- Eastgate: Most affordable rent at $7/sqft; lower customer proximity (25% within 2 hrs), solid labor market, limited expansion area [facts: F5, F6]
Assumptions:
A1. Northfield's transport infrastructure allows easy access to customers.
A2. Riverside does not have a skilled local workforce but may offer employees from surrounding areas or through relocation incentives and training programs.
A3. Eastgate will benefit significantly if the planned highway is built, potentially improving customer proximity.
Open questions:
Q1. How might Northfield's unemployment rate influence labor costs despite lower rent?
Q2. What are Riverside's potential transport links to other areas for hiring and goods distribution?
Q3. If Eastgate develops the highway, how will it impact customer reach within 2 hours?

## Step 2: deliberation

### Round 0

```
Advocate (round 0, prefers Eastgate): With careful consideration of potential uncertainties and constraints, Eastgate offers a compelling balance for the ware
  ADV0.1: Affordable rent ($7 per square foot) [no fact]
  ADV0.2: Reasonable labor market (4% unemployment, 1 logistics school available) and limited expansion area [F6]
Skeptic (round 0, prefers Eastgate): Though Eastgate currently has lower customer proximity compared to Northfield and Riverside, its most significant pluses
  SKE0.1: Affordable rent is a critical factor for the initial investment in setting up a new warehouse. Eastg [no fact]
  SKE0.2: The presence of logistics training (F6) would significantly reduce labor costs and difficulties, en# [F6]
Analyst (round 0, prefers Eastgate): Though Eastgate currently has lower customer proximity than Northfield, its affordable rent combined with the presence a
  ANA0.1: fact F5 (rent is $7 per square foot) [F5]
  ANA0.2: fact F6 (4% unemployment and 1 logistics school [F6]
```

### Round 1

```
Advocate (round 1, prefers Eastgate): Considering the potential for significant improvement in customer proximity if Eastgate's planned highway is built and t
  ADV1.1: Higher rent at Northfield ($9 per square foot) might not justify its marginal advantage over other w [no fact]
  ADV1.2: Riverside's higher costs and lack of local skilled labor could pose a problem, despite having no un [F4]
Skeptic (round 1, prefers Eastgate): I understand the appeal of Eastgate's lower rent; however, I have reservations about its reliance on uncertain developm#
  SKE1.1: Skeptic (round 0) accepts claim F6 [F5]
Analyst (round 1, prefers Eastgate): With careful consideration of all factors and potential developments, I now prefer Eastgate for opening our new warehous
  ANA1.1: Given the uncertainties about a planned highway near Eastgate that could improve customer proximity. [F5]
  ANA1.2: The affordability of rent in Eastgate, which is significantly lower than both Northfield and Rivers [F5]
```

### Round 2

```
Advocate (round 2, prefers Eastgate): Considering the potential for significant improvement in customer proximity if Eastgate's planned highway is built and t
  ADV2.1: While Northfield has a lower rent ($9 per square foot) and high current customer reach (70% within 2 [F1, F5]
  ADV2.2: Eastgate's most affordable option at $7/sqft provides the best opportunity for cost savings on rent. [F4, F5]
Skeptic (round 2, prefers Northfield): Although Eastgate presents the lowest rent option which initially seems attractive for cost-saving on warehouse space, I
  SKE2.1: A1. Northfield's transport infrastructure allows easy access to customers. [no fact]
  SKE2.2: Q2. What are Riverside's potential transport links to other areas for hiring and goods distribution? [F1]
Analyst (round 2, prefers Eastgate): Despite its current lower customer proximity and limited expansion area due to space constraints (F5), Eastgate's low-r[
  ANA2.1: The affordability of rent in Northfield, which is significantly lower than both Riverside and East [F1]
```

## Step 3: judge

Arguments the Judge cited per criterion: rent: none; proximity: SKE2.1, ANA2.1; labor: none; expansion: none

| option | expected | low | high |
|---|---|---|---|
| Northfield | 7.83 | 6 | 9.35 |
| Eastgate | 6.93 | 5.45 | 8.5 |
| Riverside | 6.38 | 5.3 | 7.75 |

1. Northfield: 7.83 (range 6.00-9.35)
2. Eastgate: 6.93 (range 5.45-8.50)
3. Riverside: 6.38 (range 5.30-7.75)
Margin of Northfield over Eastgate: 0.90
Smallest weight change that flips the top choice: rent weight 0.30 -> 0.58 (Eastgate overtakes)
Smallest score change that flips it: Northfield on proximity 9.0 -> 6.4 (Eastgate overtakes)
