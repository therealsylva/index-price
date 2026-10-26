# Football index forward update — 2026-10-26T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-10-22T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-10-26T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **46** (46 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **1264/1433** (88.2%)
- Clubs repriced: **92**
- Players repriced: **1264**
- Unmapped player appearances held (never identity-guessed): **169**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Elche CF | 1004.899 | 1056.140 | +5.10% | 1 |
| Borussia VfL Mönchengladbach | 1173.661 | 1232.711 | +5.03% | 1 |
| SV Werder Bremen | 1406.156 | 1474.097 | +4.83% | 1 |
| AFC Bournemouth | 1919.235 | 2005.512 | +4.50% | 1 |
| Real Madrid CF | 6307.930 | 6560.728 | +4.01% | 1 |
| Real Racing Club | 976.291 | 1013.778 | +3.84% | 1 |
| OGC Nice Côte d'Azur | 1327.242 | 1378.071 | +3.83% | 1 |
| Tottenham Hotspur FC | 1920.916 | 1987.936 | +3.49% | 1 |
| Newcastle United FC | 1716.097 | 1774.693 | +3.41% | 1 |
| Bologna FC 1909 | 1220.863 | 1261.337 | +3.32% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Rayo Vallecano de Madrid | 1869.898 | 1803.879 | -3.53% | 1 |
| Bayer 04 Leverkusen | 3267.347 | 3156.102 | -3.40% | 1 |
| Chelsea FC | 1850.134 | 1789.297 | -3.29% | 1 |
| Cagliari Calcio | 789.360 | 766.588 | -2.88% | 1 |
| Stade Brestois 29 | 1438.352 | 1397.161 | -2.86% | 1 |
| VfB Stuttgart 1893 | 2341.347 | 2274.370 | -2.86% | 1 |
| Manchester United FC | 2227.428 | 2163.717 | -2.86% | 1 |
| Toulouse FC | 1558.107 | 1515.895 | -2.71% | 1 |
| FC Barcelona | 6124.413 | 5959.433 | -2.69% | 1 |
| US Lecce | 804.573 | 783.213 | -2.65% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Ángel Fortuno | 1063.974 | 1093.358 | +2.76% | 1 |
| Justin Bijlow | 1287.892 | 1320.545 | +2.54% | 1 |
| Zion Suzuki | 1094.111 | 1120.975 | +2.46% | 1 |
| David de Gea | 790.135 | 809.076 | +2.40% | 1 |
| James Trafford | 1222.017 | 1249.754 | +2.27% | 1 |
| Matías Dituro | 1464.415 | 1496.847 | +2.21% | 1 |
| Jan Oblak | 799.138 | 816.762 | +2.21% | 1 |
| Andriy Lunin | 1290.404 | 1318.625 | +2.19% | 1 |
| Pablo Ramón | 1062.691 | 1085.187 | +2.12% | 1 |
| Mike Maignan | 2674.869 | 2730.625 | +2.08% | 1 |
| Abdukodir Khusanov | 1430.332 | 1460.037 | +2.08% | 1 |
| Mamadou Sangaré | 1486.908 | 1517.740 | +2.07% | 1 |
| Marco Carnesecchi | 1069.723 | 1091.114 | +2.00% | 1 |
| Álvaro Vallés | 1705.059 | 1738.855 | +1.98% | 1 |
| Berke Özer | 974.387 | 993.195 | +1.93% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| David Soria | 558.589 | 544.303 | -2.56% | 1 |
| Gauthier Gallon | 1116.798 | 1092.879 | -2.14% | 1 |
| Walter Benítez | 1203.870 | 1179.569 | -2.02% | 1 |
| Gianluigi Donnarumma | 1708.227 | 1673.805 | -2.02% | 1 |
| Anthony Lopes | 1523.332 | 1493.297 | -1.97% | 1 |
| Robin Risser | 904.677 | 887.524 | -1.90% | 1 |
| Valde | 981.932 | 963.368 | -1.89% | 1 |
| Wladimiro Falcone | 600.682 | 589.618 | -1.84% | 1 |
| Paul Nardi | 899.315 | 882.935 | -1.82% | 1 |
| Guillaume Restes | 540.997 | 532.578 | -1.56% | 1 |
| Alex Meret | 1100.621 | 1084.038 | -1.51% | 1 |
| Julen Agirrezabala | 1001.588 | 986.523 | -1.50% | 1 |
| Lukás Hrádecky | 815.233 | 803.107 | -1.49% | 1 |
| Jean Butez | 1684.702 | 1659.981 | -1.47% | 1 |
| Keane Lewis-Potter | 834.932 | 823.514 | -1.37% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
