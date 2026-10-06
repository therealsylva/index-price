# Football index forward update — 2026-10-06T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-09-01T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-10-06T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **153** (153 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **4225/4807** (87.9%)
- Clubs repriced: **96**
- Players repriced: **1623**
- Unmapped player appearances held (never identity-guessed): **582**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Cagliari Calcio | 736.845 | 807.056 | +9.53% | 3 |
| FC Barcelona | 5373.099 | 5826.017 | +8.43% | 4 |
| BV Borussia 09 Dortmund | 2846.258 | 3084.347 | +8.36% | 3 |
| Real Betis Balompié | 2866.310 | 3105.008 | +8.33% | 4 |
| Paris FC | 1115.010 | 1201.309 | +7.74% | 3 |
| SV Werder Bremen | 1297.677 | 1396.026 | +7.58% | 3 |
| Manchester City FC | 2536.253 | 2704.999 | +6.65% | 3 |
| Frosinone Calcio | 1072.447 | 1142.508 | +6.53% | 3 |
| SS Lazio | 1325.875 | 1406.895 | +6.11% | 3 |
| 1. FSV Mainz 05 | 1337.381 | 1417.920 | +6.02% | 3 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Atalanta Bergamasca Calcio | 2548.511 | 2338.388 | -8.24% | 3 |
| Borussia VfL Mönchengladbach | 1317.610 | 1235.262 | -6.25% | 3 |
| Malaga | 964.769 | 906.303 | -6.06% | 4 |
| CA Osasuna | 815.340 | 766.714 | -5.96% | 4 |
| Udinese Calcio | 953.086 | 897.200 | -5.86% | 3 |
| Olympique de Marseille | 2289.955 | 2156.805 | -5.81% | 3 |
| Racing Club de Lens | 2403.479 | 2269.108 | -5.59% | 3 |
| Espérance Sportive Troyes Aube Champagne | 920.745 | 870.221 | -5.49% | 3 |
| Venezia FC | 667.033 | 631.511 | -5.33% | 3 |
| Tottenham Hotspur FC | 1985.169 | 1882.465 | -5.17% | 3 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Álvaro Vallés | 1540.366 | 1670.592 | +8.45% | 4 |
| Christos Mandas | 1056.466 | 1129.132 | +6.88% | 3 |
| Lamine Yamal | 2631.047 | 2800.525 | +6.44% | 4 |
| Cristian Cásseres | 1382.606 | 1467.823 | +6.16% | 3 |
| Zion Suzuki | 1041.746 | 1097.837 | +5.38% | 3 |
| Murillo | 1290.988 | 1358.457 | +5.23% | 3 |
| Thibaut Courtois | 2846.347 | 2988.203 | +4.98% | 4 |
| Jeffrey De Lange | 957.439 | 1004.821 | +4.95% | 3 |
| Aleix García | 2557.148 | 2681.885 | +4.88% | 3 |
| Leo Román | 1184.100 | 1239.980 | +4.72% | 4 |
| James Trafford | 1162.721 | 1216.136 | +4.59% | 3 |
| David Soria | 519.075 | 542.684 | +4.55% | 4 |
| Nicolò Fagioli | 1553.146 | 1622.840 | +4.49% | 3 |
| Vítinha | 3994.622 | 4170.441 | +4.40% | 3 |
| Nico Paz | 1697.881 | 1772.210 | +4.38% | 3 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Djordje Petrović | 1280.415 | 1220.299 | -4.70% | 3 |
| Robin Roefs | 1005.135 | 968.944 | -3.60% | 3 |
| Kevin Trapp | 574.242 | 557.103 | -2.98% | 3 |
| Gauthier Gallon | 1185.089 | 1149.865 | -2.97% | 3 |
| Thomas Meunier | 1137.133 | 1106.302 | -2.71% | 3 |
| Guglielmo Vicario | 1588.776 | 1548.373 | -2.54% | 3 |
| Leif Davis | 853.823 | 832.531 | -2.49% | 3 |
| Nemanja Gudelj | 1385.430 | 1352.265 | -2.39% | 4 |
| Elias Jelert | 958.629 | 936.392 | -2.32% | 3 |
| Riccardo Calafiori | 1344.228 | 1313.646 | -2.28% | 3 |
| Luíz Júnior | 1013.248 | 990.271 | -2.27% | 1 |
| Ferdi Kadıoğlu | 981.223 | 959.227 | -2.24% | 3 |
| Richie Sagrado | 996.571 | 974.469 | -2.22% | 3 |
| Neco Williams | 1096.199 | 1072.321 | -2.18% | 3 |
| Demba Thiam | 992.628 | 971.025 | -2.18% | 2 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
