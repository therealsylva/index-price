# Football index forward update — 2026-11-15T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-11-04T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-11-15T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **93** (93 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **2564/2900** (88.4%)
- Clubs repriced: **159**
- Players repriced: **2231**
- Unmapped player appearances held (never identity-guessed): **336**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| AFC Bournemouth | 2037.129 | 2144.631 | +5.28% | 2 |
| Olympique de Marseille | 2390.031 | 2513.085 | +5.15% | 2 |
| AFC Ajax | 1046.194 | 1099.707 | +5.11% | 1 |
| BV Borussia 09 Dortmund | 3080.019 | 3225.337 | +4.72% | 2 |
| NK Celje | 1093.295 | 1143.394 | +4.58% | 1 |
| Ferencvárosi TC | 1260.484 | 1317.107 | +4.49% | 1 |
| Real Racing Club | 998.543 | 1043.375 | +4.49% | 1 |
| FC Porto | 1197.245 | 1248.352 | +4.27% | 1 |
| Club Brugge KV | 1490.870 | 1553.275 | +4.19% | 1 |
| Nottingham Forest FC | 1120.717 | 1166.981 | +4.13% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Racing Club de Lens | 2370.598 | 2254.457 | -4.90% | 2 |
| Stade Rennais FC | 2219.115 | 2112.570 | -4.80% | 2 |
| Olympique Lyonnais | 2241.027 | 2153.088 | -3.92% | 2 |
| FC Midtjylland | 1587.158 | 1531.818 | -3.49% | 1 |
| Real Club Celta de Vigo | 1252.307 | 1209.689 | -3.40% | 2 |
| Chelsea FC | 1860.004 | 1803.287 | -3.05% | 1 |
| Tottenham Hotspur FC | 2044.572 | 1982.834 | -3.02% | 1 |
| Getafe CF | 589.096 | 571.843 | -2.93% | 2 |
| Alkmaar Zaanstreek | 1701.321 | 1652.180 | -2.89% | 1 |
| Hapoel Be'er Sheva FC | 1060.372 | 1030.292 | -2.84% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Aleix García | 2822.100 | 2935.836 | +4.03% | 2 |
| Elliot Anderson | 1812.259 | 1875.352 | +3.48% | 2 |
| Elia Caprile | 1135.963 | 1174.204 | +3.37% | 1 |
| Javi Díaz | 998.312 | 1031.453 | +3.32% | 1 |
| Fedor Lapoukhov | 1036.472 | 1070.495 | +3.28% | 1 |
| Mathew Ryan | 1299.868 | 1340.306 | +3.11% | 1 |
| Konstantinos Tzolakis | 955.930 | 984.337 | +2.97% | 1 |
| Marc Cucurella | 1496.514 | 1540.051 | +2.91% | 2 |
| Koni De Winter | 1237.035 | 1272.369 | +2.86% | 2 |
| Sergio Carreira | 1111.074 | 1142.151 | +2.80% | 2 |
| Luis Milla | 1860.190 | 1912.174 | +2.79% | 2 |
| Marco Carnesecchi | 1062.640 | 1092.323 | +2.79% | 2 |
| David Raum | 1102.300 | 1132.314 | +2.72% | 2 |
| Corentin Tolisso | 2105.018 | 2161.327 | +2.68% | 2 |
| Jeffrey De Lange | 1012.985 | 1039.830 | +2.65% | 2 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Robin Risser | 905.474 | 883.369 | -2.44% | 2 |
| Arnaud Bodart | 993.494 | 971.325 | -2.23% | 1 |
| Ionuț Radu | 1060.436 | 1037.509 | -2.16% | 2 |
| Justin Bijlow | 1376.194 | 1347.219 | -2.11% | 1 |
| Giacomo Quagliata | 955.695 | 939.828 | -1.66% | 1 |
| Toni Silić | 1000.654 | 984.281 | -1.64% | 1 |
| Mahdi Camara | 1204.189 | 1185.355 | -1.56% | 2 |
| Djordje Petrović | 1178.170 | 1159.909 | -1.55% | 1 |
| Berke Özer | 1005.516 | 990.376 | -1.51% | 1 |
| Finn Dahmen | 1091.537 | 1075.593 | -1.46% | 1 |
| Łukasz Skorupski | 1185.829 | 1168.789 | -1.44% | 1 |
| Ville Koski | 991.463 | 977.430 | -1.42% | 1 |
| Mike Penders | 1545.245 | 1523.845 | -1.38% | 1 |
| Ali Maamar | 989.096 | 976.551 | -1.27% | 1 |
| Devis Vásquez | 831.472 | 820.973 | -1.26% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
