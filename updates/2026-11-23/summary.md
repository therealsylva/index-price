# Football index forward update — 2026-11-23T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-11-15T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-11-23T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **45** (45 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **1234/1415** (87.2%)
- Clubs repriced: **90**
- Players repriced: **1234**
- Unmapped player appearances held (never identity-guessed): **181**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Le Mans | 963.216 | 1010.706 | +4.93% | 1 |
| Leeds United FC | 1066.698 | 1118.109 | +4.82% | 1 |
| Valencia CF | 892.275 | 931.698 | +4.42% | 1 |
| Stade Brestois 29 | 1484.018 | 1544.570 | +4.08% | 1 |
| Genoa CFC | 781.132 | 812.161 | +3.97% | 1 |
| RasenBallsport Leipzig | 2519.872 | 2618.464 | +3.91% | 1 |
| FC Augsburg | 967.194 | 1005.018 | +3.91% | 1 |
| Reial Club Deportiu Espanyol de Barcelona | 1071.030 | 1112.611 | +3.88% | 1 |
| Real Racing Club | 1043.375 | 1083.214 | +3.82% | 1 |
| Hull City | 995.915 | 1033.902 | +3.81% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Rayo Vallecano de Madrid | 1804.890 | 1731.864 | -4.05% | 1 |
| Olympique de Marseille | 2513.085 | 2426.185 | -3.46% | 1 |
| Chelsea FC | 1803.287 | 1743.883 | -3.29% | 1 |
| Athletic Club | 1404.483 | 1358.920 | -3.24% | 1 |
| FC Bayern München | 8925.310 | 8648.606 | -3.10% | 1 |
| RC Strasbourg Alsace | 1488.707 | 1444.024 | -3.00% | 1 |
| SV Elversberg | 1085.332 | 1053.794 | -2.91% | 1 |
| Malaga | 861.814 | 838.741 | -2.68% | 1 |
| Brighton & Hove Albion FC | 2108.945 | 2057.199 | -2.45% | 1 |
| AS Monaco FC | 2733.400 | 2666.468 | -2.45% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Ángel Fortuño | 1128.004 | 1165.982 | +3.37% | 1 |
| Robin Roefs | 960.148 | 990.351 | +3.15% | 1 |
| Konstantinos Tzolakis | 984.337 | 1011.725 | +2.78% | 1 |
| Lucas Perri | 922.380 | 947.924 | +2.77% | 1 |
| Justin Bijlow | 1347.219 | 1384.055 | +2.73% | 1 |
| Christian Walton | 944.697 | 970.132 | +2.69% | 1 |
| Guillaume Restes | 524.686 | 537.413 | +2.43% | 1 |
| Pedri | 2961.781 | 3032.241 | +2.38% | 1 |
| Dominik Greif | 1132.138 | 1158.613 | +2.34% | 1 |
| Sergio Gómez | 1211.971 | 1239.099 | +2.24% | 1 |
| Willi Orbán | 2557.540 | 2612.297 | +2.14% | 1 |
| Maarten Vandevoordt | 1094.451 | 1117.504 | +2.11% | 1 |
| Rio Ngumoha | 1037.063 | 1058.876 | +2.10% | 1 |
| Gleison Bremer | 2423.072 | 2473.495 | +2.08% | 1 |
| Dominik Szoboszlai | 3454.671 | 3525.833 | +2.06% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Matvey Safonov | 910.798 | 892.286 | -2.03% | 1 |
| Joan García | 1707.842 | 1674.076 | -1.98% | 1 |
| Lukás Hrádecky | 820.473 | 806.068 | -1.76% | 1 |
| Marco Sportiello | 1052.177 | 1034.059 | -1.72% | 1 |
| Yéhvann Diouf | 1856.689 | 1826.421 | -1.63% | 1 |
| Aitor Ruibal | 1378.413 | 1358.051 | -1.48% | 1 |
| Darnell Furlong | 1002.121 | 987.569 | -1.45% | 1 |
| Sergio Herrera | 1331.549 | 1312.213 | -1.45% | 1 |
| Arijanet Murić | 1586.124 | 1563.462 | -1.43% | 1 |
| Filip Jörgensen | 1648.439 | 1626.218 | -1.35% | 1 |
| Niko Sigur | 981.852 | 968.837 | -1.33% | 1 |
| Luke O'Nien | 984.691 | 972.594 | -1.23% | 1 |
| Alessio Cacciamani | 965.125 | 953.471 | -1.21% | 1 |
| Zakaria El Ouahdi | 1052.936 | 1040.289 | -1.20% | 1 |
| Nathaniel Brown | 995.070 | 983.644 | -1.15% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
