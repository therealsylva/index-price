# Football index forward update — 2026-11-04T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-11-01T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-11-04T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **21** (21 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **575/658** (87.4%)
- Clubs repriced: **42**
- Players repriced: **575**
- Unmapped player appearances held (never identity-guessed): **83**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Parma Calcio 1913 | 950.356 | 999.941 | +5.22% | 1 |
| Paris FC | 1209.171 | 1264.882 | +4.61% | 1 |
| Everton FC | 948.742 | 988.811 | +4.22% | 1 |
| Arsenal FC | 2877.193 | 2991.500 | +3.97% | 1 |
| Getafe CF | 568.580 | 589.152 | +3.62% | 1 |
| Valencia CF | 875.977 | 905.940 | +3.42% | 1 |
| ACF Fiorentina | 1176.839 | 1217.065 | +3.42% | 1 |
| Eintracht Frankfurt | 1233.346 | 1275.039 | +3.38% | 1 |
| RC Strasbourg Alsace | 1478.657 | 1527.847 | +3.33% | 1 |
| Stade Brestois 29 | 1397.161 | 1441.171 | +3.15% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Atalanta Bergamasca Calcio | 2317.077 | 2225.680 | -3.94% | 1 |
| Newcastle United FC | 1774.693 | 1705.314 | -3.91% | 1 |
| Elche CF | 1056.140 | 1019.743 | -3.45% | 1 |
| Liverpool FC | 3513.806 | 3392.810 | -3.44% | 1 |
| AS Monaco FC | 2819.018 | 2728.657 | -3.21% | 1 |
| SSC Napoli | 1806.842 | 1755.002 | -2.87% | 1 |
| FC Lorient | 1181.296 | 1150.348 | -2.62% | 1 |
| Association Jeunesse Auxerroise | 1017.582 | 993.149 | -2.40% | 1 |
| Sevilla FC | 892.212 | 871.579 | -2.31% | 1 |
| US Lecce | 772.178 | 755.804 | -2.12% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Jeffrey De Lange | 986.523 | 1012.985 | +2.68% | 1 |
| Justin Bijlow | 1342.584 | 1376.195 | +2.50% | 1 |
| Unai Simón | 891.155 | 910.871 | +2.21% | 1 |
| Corentin Tolisso | 2060.872 | 2103.670 | +2.08% | 1 |
| Nemanja Matić | 2300.882 | 2347.948 | +2.05% | 1 |
| Arthur Avom | 1168.902 | 1192.619 | +2.03% | 1 |
| Jude Bellingham | 3824.863 | 3902.319 | +2.03% | 1 |
| Tom Krauß | 1235.151 | 1260.078 | +2.02% | 1 |
| Sergio Herrera | 1305.279 | 1331.550 | +2.01% | 1 |
| Daniel Heuer Fernandes | 1134.119 | 1156.691 | +1.99% | 1 |
| Lukás Hrádecky | 803.107 | 818.443 | +1.91% | 1 |
| Sebastián Boselli | 1003.152 | 1021.763 | +1.86% | 1 |
| Gessime Yassine | 985.815 | 1004.008 | +1.85% | 1 |
| Luis Milla | 1826.839 | 1860.190 | +1.83% | 1 |
| Lassine Sinayoko | 1305.494 | 1326.558 | +1.61% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Paul Nardi | 882.935 | 860.754 | -2.51% | 1 |
| Marco Carnesecchi | 1086.600 | 1062.640 | -2.21% | 1 |
| David de Gea | 809.599 | 792.868 | -2.07% | 1 |
| Guillaume Restes | 532.578 | 523.475 | -1.71% | 1 |
| Wladimiro Falcone | 590.272 | 580.375 | -1.68% | 1 |
| Jeanuël Belocian | 1015.700 | 998.995 | -1.64% | 1 |
| Stefano Turati | 982.051 | 967.288 | -1.50% | 1 |
| Filip Jörgensen | 1688.577 | 1668.335 | -1.20% | 1 |
| Yassin Belkhdim | 1014.096 | 1002.042 | -1.19% | 1 |
| Yvon Mvogo | 1293.744 | 1280.107 | -1.05% | 1 |
| Flavien Boyomo | 1186.129 | 1173.668 | -1.05% | 1 |
| David Raya | 888.970 | 879.760 | -1.04% | 1 |
| Alessandro Romano | 1036.975 | 1026.250 | -1.03% | 1 |
| Christos Tzolis | 1164.917 | 1153.185 | -1.01% | 1 |
| Sebastian Walukiewicz | 927.267 | 918.634 | -0.93% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
