# Football index forward update — 2026-11-04T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-11-01T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-11-04T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **30** (30 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **835/939** (88.9%)
- Clubs repriced: **60**
- Players repriced: **835**
- Unmapped player appearances held (never identity-guessed): **104**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Parma Calcio 1913 | 950.356 | 999.848 | +5.21% | 1 |
| Paris FC | 1209.171 | 1264.908 | +4.61% | 1 |
| Everton FC | 948.742 | 988.788 | +4.22% | 1 |
| Arsenal FC | 2877.193 | 2991.649 | +3.98% | 1 |
| Linzer Athletik Sport Klub | 1018.650 | 1057.429 | +3.81% | 1 |
| Manchester United FC | 2123.408 | 2201.399 | +3.67% | 1 |
| Getafe CF | 568.580 | 589.096 | +3.61% | 1 |
| Galatasaray Spor Kulübü | 1519.934 | 1574.062 | +3.56% | 1 |
| FC Internazionale Milano | 3176.920 | 3286.567 | +3.45% | 1 |
| ACF Fiorentina | 1176.839 | 1217.085 | +3.42% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Atalanta Bergamasca Calcio | 2317.077 | 2225.520 | -3.95% | 1 |
| Newcastle United FC | 1774.693 | 1705.209 | -3.92% | 1 |
| Elche CF | 1056.140 | 1019.691 | -3.45% | 1 |
| Liverpool FC | 3513.806 | 3392.581 | -3.45% | 1 |
| AS Monaco FC | 2819.018 | 2728.725 | -3.20% | 1 |
| SSC Napoli | 1806.842 | 1755.025 | -2.87% | 1 |
| FC Lorient | 1181.296 | 1150.269 | -2.63% | 1 |
| FC Shakhtar Donetsk | 898.877 | 875.751 | -2.57% | 1 |
| VfB Stuttgart 1893 | 2385.995 | 2326.563 | -2.49% | 1 |
| Association Jeunesse Auxerroise | 1017.582 | 993.119 | -2.40% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Jeffrey De Lange | 986.523 | 1012.985 | +2.68% | 1 |
| Justin Bijlow | 1342.584 | 1376.194 | +2.50% | 1 |
| Bruno Fernandes | 6677.063 | 6827.264 | +2.25% | 1 |
| João Neves | 1914.789 | 1957.293 | +2.22% | 1 |
| Unai Simón | 891.155 | 910.885 | +2.21% | 1 |
| Corentin Tolisso | 2060.872 | 2105.018 | +2.14% | 1 |
| Jude Bellingham | 3824.863 | 3903.583 | +2.06% | 1 |
| Arthur Avom | 1168.902 | 1192.942 | +2.06% | 1 |
| Nemanja Matić | 2300.882 | 2347.947 | +2.05% | 1 |
| Sergio Herrera | 1305.279 | 1331.549 | +2.01% | 1 |
| Daniel Heuer Fernandes | 1134.119 | 1156.691 | +1.99% | 1 |
| Tom Krauß | 1235.151 | 1259.215 | +1.95% | 1 |
| Lukás Hrádecky | 803.107 | 818.443 | +1.91% | 1 |
| Lukas Jungwirth | 996.854 | 1015.476 | +1.87% | 1 |
| Gessime Yassine | 985.815 | 1004.146 | +1.86% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Paul Nardi | 882.935 | 860.754 | -2.51% | 1 |
| Marco Carnesecchi | 1086.600 | 1062.640 | -2.21% | 1 |
| David de Gea | 809.599 | 792.867 | -2.07% | 1 |
| Guillaume Restes | 532.578 | 523.475 | -1.71% | 1 |
| Wladimiro Falcone | 590.272 | 580.375 | -1.68% | 1 |
| Jeanuël Belocian | 1015.700 | 999.245 | -1.62% | 1 |
| Stefano Turati | 982.051 | 967.288 | -1.50% | 1 |
| Yassin Belkhdim | 1014.096 | 1001.923 | -1.20% | 1 |
| Filip Jörgensen | 1688.577 | 1668.334 | -1.20% | 1 |
| Devis Vásquez | 841.495 | 831.472 | -1.19% | 1 |
| Jamie Leweling | 1314.155 | 1299.724 | -1.10% | 1 |
| Yvon Mvogo | 1293.744 | 1280.106 | -1.05% | 1 |
| Flavien Boyomo | 1186.129 | 1173.665 | -1.05% | 1 |
| David Raya | 888.970 | 879.760 | -1.04% | 1 |
| Alessandro Romano | 1036.975 | 1026.250 | -1.03% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
