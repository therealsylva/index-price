# Football index forward update — 2026-11-26T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-11-23T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-11-26T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **21** (21 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **586/649** (90.3%)
- Clubs repriced: **42**
- Players repriced: **586**
- Unmapped player appearances held (never identity-guessed): **63**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Lille OSC | 1434.002 | 1509.797 | +5.29% | 1 |
| AC Monza | 573.109 | 599.561 | +4.62% | 1 |
| FC Porto | 1248.352 | 1298.102 | +3.99% | 1 |
| Real Betis Balompié | 3100.812 | 3192.623 | +2.96% | 1 |
| Fenerbahçe Spor Kulübü | 1620.910 | 1666.704 | +2.83% | 1 |
| Liverpool FC | 3527.418 | 3624.389 | +2.75% | 1 |
| Villarreal CF | 1717.360 | 1764.029 | +2.72% | 1 |
| Brentford FC | 1541.465 | 1582.277 | +2.65% | 1 |
| FC Internazionale Milano | 3354.698 | 3435.938 | +2.42% | 1 |
| RasenBallsport Leipzig | 2618.464 | 2677.061 | +2.24% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Feyenoord Rotterdam | 1508.416 | 1461.095 | -3.14% | 1 |
| FC Bayern München | 8648.606 | 8385.409 | -3.04% | 1 |
| ACF Fiorentina | 1216.740 | 1182.998 | -2.77% | 1 |
| Aston Villa FC | 1544.754 | 1504.284 | -2.62% | 1 |
| SK Slavia Praha | 890.458 | 867.158 | -2.62% | 1 |
| FC Shakhtar Donetsk | 875.751 | 855.051 | -2.36% | 1 |
| Linzer Athletik Sport Klub | 1057.429 | 1033.283 | -2.28% | 1 |
| ŠK Slovan Bratislava | 913.092 | 893.919 | -2.10% | 1 |
| AEK Athens FC | 1218.673 | 1193.489 | -2.07% | 1 |
| Paris Saint-Germain FC | 6855.529 | 6719.442 | -1.99% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Demba Thiam | 971.025 | 1007.659 | +3.77% | 1 |
| Lubomír Belko | 1000.000 | 1022.692 | +2.27% | 1 |
| Mikkel Damsgaard | 1380.403 | 1408.737 | +2.05% | 1 |
| Dayot Upamecano | 4144.863 | 4229.787 | +2.05% | 1 |
| Berke Özer | 1007.569 | 1026.553 | +1.88% | 1 |
| Kylian Mbappé | 6453.590 | 6575.175 | +1.88% | 1 |
| Patrick Berg | 1610.751 | 1641.071 | +1.88% | 1 |
| Stas Pokatilov | 918.852 | 935.989 | +1.87% | 1 |
| Andrea Carboni | 1014.620 | 1033.309 | +1.84% | 1 |
| Diogo Costa | 1317.354 | 1340.377 | +1.75% | 1 |
| Mario Hermoso | 1762.889 | 1793.591 | +1.74% | 1 |
| Lazaros Rota | 1072.556 | 1091.218 | +1.74% | 1 |
| Luis Milla | 1919.193 | 1952.061 | +1.71% | 1 |
| Jeff Chabot | 2048.834 | 2083.583 | +1.70% | 1 |
| Miloš Kerkez | 848.891 | 863.170 | +1.68% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Konrad Laimer | 1233.046 | 1215.521 | -1.42% | 1 |
| Alisson Santana | 997.182 | 984.265 | -1.30% | 1 |
| Abdülkerim Bardakci | 1181.356 | 1166.249 | -1.28% | 1 |
| David de Gea | 800.040 | 790.340 | -1.21% | 1 |
| Stavros Pilios | 1013.419 | 1001.294 | -1.20% | 1 |
| Nélson Semedo | 1062.289 | 1049.697 | -1.19% | 1 |
| Yann Sommer | 1940.237 | 1917.302 | -1.18% | 1 |
| Achraf Hakimi | 1628.163 | 1609.705 | -1.13% | 1 |
| Milan Škriniar | 1796.072 | 1776.101 | -1.11% | 1 |
| Lukas Jungwirth | 1015.476 | 1004.458 | -1.08% | 1 |
| Mathew Ryan | 1340.306 | 1326.172 | -1.05% | 1 |
| Nahuel Molina | 1083.398 | 1072.031 | -1.05% | 1 |
| Eren Elmalı | 977.538 | 967.442 | -1.03% | 1 |
| Uğurcan Çakır | 1037.135 | 1026.648 | -1.01% | 1 |
| Alberto Costa | 1033.608 | 1023.200 | -1.01% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
