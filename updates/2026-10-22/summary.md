# Football index forward update — 2026-10-22T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-10-06T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-10-22T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **96** (96 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **2648/3011** (87.9%)
- Clubs repriced: **96**
- Players repriced: **1542**
- Unmapped player appearances held (never identity-guessed): **363**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Real Sociedad de Fútbol | 1120.073 | 1203.270 | +7.43% | 2 |
| Hamburger SV | 1081.384 | 1157.812 | +7.07% | 2 |
| FC Lorient | 1119.782 | 1194.563 | +6.68% | 2 |
| Torino FC | 812.008 | 863.352 | +6.32% | 2 |
| Brighton & Hove Albion FC | 1856.030 | 1973.037 | +6.30% | 2 |
| Chelsea FC | 1741.225 | 1850.134 | +6.25% | 2 |
| SS Lazio | 1406.895 | 1490.582 | +5.95% | 2 |
| Racing Club de Lens | 2269.108 | 2402.483 | +5.88% | 2 |
| Manchester City FC | 2704.999 | 2859.686 | +5.72% | 2 |
| Olympique de Marseille | 2156.805 | 2274.227 | +5.44% | 2 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Newcastle United FC | 1813.192 | 1716.097 | -5.35% | 2 |
| Sunderland AFC | 1311.113 | 1243.863 | -5.13% | 2 |
| Udinese Calcio | 897.200 | 851.863 | -5.05% | 2 |
| Borussia VfL Mönchengladbach | 1235.262 | 1173.661 | -4.99% | 2 |
| ACF Fiorentina | 1248.168 | 1188.820 | -4.75% | 2 |
| AS Monaco FC | 3010.462 | 2870.069 | -4.66% | 2 |
| Parma Calcio 1913 | 1024.801 | 980.660 | -4.31% | 2 |
| Le Mans | 1020.766 | 978.808 | -4.11% | 2 |
| Espérance Sportive Troyes Aube Champagne | 870.221 | 834.504 | -4.10% | 2 |
| FC Schalke 04 | 1046.256 | 1003.723 | -4.07% | 2 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Ángel Fortuno | 1007.449 | 1063.974 | +5.61% | 2 |
| Filip Stanković | 1093.163 | 1153.251 | +5.50% | 2 |
| Maarten Vandevoordt | 1038.071 | 1084.870 | +4.51% | 2 |
| Arijanet Murić | 1498.683 | 1566.205 | +4.51% | 2 |
| Waldemar Anton | 2498.776 | 2592.706 | +3.76% | 2 |
| Iñigo Vicente | 1069.787 | 1109.873 | +3.75% | 2 |
| Konstantinos Tzolakis | 920.187 | 952.301 | +3.49% | 2 |
| Alex Remiro | 1587.309 | 1641.736 | +3.43% | 2 |
| Thibaut Courtois | 2988.203 | 3088.707 | +3.36% | 2 |
| Ionuț Radu | 1006.866 | 1039.523 | +3.24% | 2 |
| Jon Martín | 1194.096 | 1232.001 | +3.17% | 2 |
| Aleix García | 2681.885 | 2766.426 | +3.15% | 2 |
| Angelo Stiller | 2135.079 | 2201.242 | +3.10% | 2 |
| Mathew Ryan | 1269.030 | 1308.307 | +3.10% | 3 |
| Declan Rice | 3887.149 | 4005.662 | +3.05% | 2 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Djordje Petrović | 1220.299 | 1174.609 | -3.74% | 2 |
| Alisson Becker | 2257.581 | 2173.272 | -3.73% | 2 |
| Guglielmo Vicario | 1548.373 | 1491.975 | -3.64% | 2 |
| Gauthier Gallon | 1149.865 | 1116.798 | -2.88% | 2 |
| Lukás Hornícek | 1023.376 | 996.848 | -2.59% | 2 |
| Jeremy Toljan | 648.887 | 633.275 | -2.41% | 3 |
| Foe Ondoa | 907.697 | 886.015 | -2.39% | 2 |
| Edoardo Corvi | 1131.605 | 1106.480 | -2.22% | 2 |
| Lukás Hrádecky | 833.172 | 815.233 | -2.15% | 2 |
| Giacomo Quagliata | 988.287 | 968.284 | -2.02% | 2 |
| Keane Lewis-Potter | 851.665 | 834.932 | -1.96% | 2 |
| Yéhvann Diouf | 1791.498 | 1757.926 | -1.87% | 2 |
| Antonín Kinský | 926.236 | 910.250 | -1.73% | 2 |
| Ethan Pinnock | 1370.119 | 1346.586 | -1.72% | 2 |
| Gautier Lloris | 1238.426 | 1217.501 | -1.69% | 2 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
