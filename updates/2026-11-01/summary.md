# Football index forward update — 2026-11-01T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-10-26T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-11-01T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **39** (39 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **1079/1225** (88.1%)
- Clubs repriced: **71**
- Players repriced: **992**
- Unmapped player appearances held (never identity-guessed): **146**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| AS Roma | 2202.541 | 2320.078 | +5.34% | 2 |
| VfB Stuttgart 1893 | 2274.370 | 2385.995 | +4.91% | 1 |
| Bologna FC 1909 | 1261.337 | 1318.944 | +4.57% | 2 |
| Reial Club Deportiu Espanyol de Barcelona | 1044.914 | 1091.527 | +4.46% | 1 |
| Paris Saint-Germain FC | 6202.314 | 6476.805 | +4.43% | 2 |
| Brighton & Hove Albion FC | 1941.415 | 2025.531 | +4.33% | 1 |
| Chelsea FC | 1789.297 | 1860.004 | +3.95% | 1 |
| Frosinone Calcio | 1181.360 | 1220.459 | +3.31% | 1 |
| SV Elversberg | 1054.570 | 1089.453 | +3.31% | 1 |
| SC Freiburg | 1598.109 | 1650.878 | +3.30% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Villarreal CF | 1798.939 | 1727.939 | -3.95% | 1 |
| AC Monza | 597.858 | 579.715 | -3.03% | 2 |
| Juventus FC | 1488.873 | 1445.159 | -2.94% | 1 |
| Manchester City FC | 2789.076 | 2707.949 | -2.91% | 1 |
| Racing Club de Lens | 2437.067 | 2370.598 | -2.73% | 1 |
| 1. FSV Mainz 05 | 1418.832 | 1380.373 | -2.71% | 1 |
| Le Mans | 983.217 | 956.987 | -2.67% | 1 |
| Bayer 04 Leverkusen | 3156.102 | 3081.724 | -2.36% | 1 |
| CA Osasuna | 789.139 | 770.749 | -2.33% | 1 |
| Sunderland AFC | 1228.377 | 1199.831 | -2.32% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Pierluigi Gollini | 985.204 | 1018.139 | +3.34% | 2 |
| Bryan Cristante | 2240.601 | 2308.578 | +3.03% | 2 |
| Bart Verbruggen | 1389.914 | 1430.641 | +2.93% | 1 |
| Ángel Fortuno | 1093.358 | 1122.022 | +2.62% | 1 |
| Senne Lammens | 765.075 | 784.970 | +2.60% | 1 |
| Warren Zaïre-Emery | 1633.292 | 1674.102 | +2.50% | 2 |
| Matias Soulé | 2013.953 | 2061.195 | +2.35% | 2 |
| Matvey Safonov | 887.821 | 908.234 | +2.30% | 2 |
| Dean Henderson | 546.963 | 559.425 | +2.28% | 1 |
| Vanja Milinković-Savić | 785.842 | 802.600 | +2.13% | 1 |
| Yéhvann Diouf | 1787.292 | 1824.180 | +2.06% | 1 |
| Aitor Fernández | 1145.051 | 1168.588 | +2.06% | 1 |
| Robin Risser | 887.524 | 905.474 | +2.02% | 1 |
| Cole Palmer | 2353.224 | 2400.252 | +2.00% | 1 |
| James McAtee | 1090.217 | 1111.971 | +2.00% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Foe Ondoa | 878.437 | 853.836 | -2.80% | 2 |
| Antonio Sivera | 554.867 | 541.867 | -2.34% | 1 |
| Matz Sels | 438.725 | 428.778 | -2.27% | 1 |
| Josep Martínez | 1099.355 | 1076.381 | -2.09% | 1 |
| Guglielmo Vicario | 1511.856 | 1481.941 | -1.98% | 1 |
| Ricardo Mangas | 921.513 | 905.578 | -1.73% | 2 |
| Stefano Turati | 998.940 | 982.051 | -1.69% | 1 |
| Christian Walton | 967.239 | 951.003 | -1.68% | 1 |
| Robin Roefs | 972.263 | 956.183 | -1.65% | 1 |
| Konstantinos Tzolakis | 969.773 | 955.930 | -1.43% | 1 |
| Antonín Kinský | 927.332 | 915.215 | -1.31% | 1 |
| Abdelhamid Aït Boudlal | 1102.335 | 1088.947 | -1.21% | 1 |
| Jonny Otto | 1102.092 | 1089.135 | -1.18% | 1 |
| Lucas Calodat | 997.143 | 985.456 | -1.17% | 1 |
| Łukasz Skorupski | 1199.803 | 1185.829 | -1.16% | 2 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
