# Football index forward update — 2026-08-30T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-08-26T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-08-30T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **71** (64 Extended; 7 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **1802/2005** (89.9%)
- Clubs repriced: **140**
- Players repriced: **1774**
- Unmapped player appearances held (never identity-guessed): **203**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| FC Twente | 1094.749 | 1152.199 | +5.25% | 1 |
| Lincoln Red Imps FC | 787.670 | 828.071 | +5.13% | 1 |
| Frosinone Calcio | 1020.921 | 1072.447 | +5.05% | 1 |
| Levante UD | 1055.387 | 1107.724 | +4.96% | 1 |
| HNK Hajduk Split | 916.954 | 960.756 | +4.78% | 1 |
| ŠK Slovan Bratislava | 888.009 | 929.925 | +4.72% | 1 |
| CA Osasuna | 767.309 | 802.556 | +4.59% | 1 |
| Fenerbahçe Spor Kulübü | 1490.981 | 1557.133 | +4.44% | 1 |
| SK Brann | 1006.234 | 1050.393 | +4.39% | 1 |
| Panathinaikos FC | 1254.883 | 1309.544 | +4.36% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Olympique Lyonnais | 2227.400 | 2112.656 | -5.15% | 2 |
| Association Jeunesse Auxerroise | 986.025 | 942.428 | -4.42% | 1 |
| Real Club Celta de Vigo | 1334.322 | 1283.640 | -3.80% | 1 |
| Larne FC | 873.455 | 841.096 | -3.70% | 1 |
| Coventry City | 979.324 | 946.415 | -3.36% | 1 |
| Trabzonspor Kulübü | 998.870 | 968.422 | -3.05% | 1 |
| FC Lorient | 1134.283 | 1101.161 | -2.92% | 1 |
| Tottenham Hotspur FC | 2044.522 | 1985.169 | -2.90% | 1 |
| Bayer 04 Leverkusen | 3093.178 | 3004.116 | -2.88% | 1 |
| Villarreal CF | 1826.249 | 1776.423 | -2.73% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Unai Simón | 837.459 | 863.333 | +3.09% | 1 |
| Antonio Sivera | 520.299 | 534.287 | +2.69% | 1 |
| João Bravim | 1000.000 | 1026.033 | +2.60% | 1 |
| Marko Dmitrovic | 904.008 | 927.474 | +2.60% | 1 |
| Filip Jörgensen | 1610.226 | 1649.708 | +2.45% | 1 |
| Iñaki Peña | 1329.972 | 1361.933 | +2.40% | 1 |
| David von Ballmoos | 942.219 | 964.557 | +2.37% | 1 |
| Marco Kana | 1000.711 | 1024.012 | +2.33% | 1 |
| Flávio Nazinho | 1010.399 | 1033.794 | +2.32% | 1 |
| Malick Fofana | 1182.792 | 1208.820 | +2.20% | 2 |
| Vítinha | 3909.472 | 3994.622 | +2.18% | 1 |
| Anthony Racioppi | 1043.651 | 1065.600 | +2.10% | 1 |
| Manuel Locatelli | 2834.429 | 2893.707 | +2.09% | 1 |
| Pablo Barrios | 1628.715 | 1662.556 | +2.08% | 1 |
| Jérémy Jacquet | 1125.299 | 1148.368 | +2.05% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Yvon Mvogo | 1249.506 | 1220.506 | -2.32% | 1 |
| Marc ter Stegen | 2626.923 | 2572.885 | -2.06% | 1 |
| Antonín Kinsky | 957.037 | 937.944 | -2.00% | 1 |
| Lars Unnerstall | 1030.927 | 1011.184 | -1.92% | 1 |
| Radoslaw Majecki | 952.508 | 934.304 | -1.91% | 1 |
| Mio Backhaus | 1089.380 | 1070.610 | -1.72% | 1 |
| Matheo Raab | 1013.258 | 995.889 | -1.71% | 1 |
| Kacper Trelowski | 991.931 | 975.896 | -1.62% | 1 |
| Alisson Becker | 2215.222 | 2180.365 | -1.57% | 1 |
| Ofek Melika | 990.657 | 975.322 | -1.55% | 1 |
| Philipp Schulze | 1007.593 | 992.296 | -1.52% | 1 |
| Alexsandro Ribeiro | 2036.392 | 2005.971 | -1.49% | 1 |
| Nathaniel Brown | 1057.702 | 1042.544 | -1.43% | 1 |
| Matvey Safonov | 899.039 | 886.548 | -1.39% | 1 |
| Justas Lasickas | 1025.275 | 1011.571 | -1.34% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
