# Football index forward update — 2026-09-01T00:00:00.000000Z

This incremental calculation starts from the published state at 2026-08-30T00:00:00.000000Z and applies only completed, in-scope competitive matches declared by the batch manifest through 2026-09-01T00:00:00.000000Z. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **20** (20 Extended; 0 BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **567/628** (90.3%)
- Clubs repriced: **40**
- Players repriced: **567**
- Unmapped player appearances held (never identity-guessed): **61**

## Biggest club rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Calcio Como 1907 | 1781.478 | 1860.197 | +4.42% | 1 |
| Athletic Club | 1356.628 | 1410.345 | +3.96% | 1 |
| Paris FC | 1072.720 | 1115.010 | +3.94% | 1 |
| FC Augsburg | 940.745 | 976.880 | +3.84% | 1 |
| RC Deportivo de La Coruña | 973.884 | 1005.608 | +3.26% | 1 |
| Sunderland AFC | 1308.429 | 1348.896 | +3.09% | 1 |
| Manchester United FC | 2288.731 | 2356.759 | +2.97% | 1 |
| FC Internazionale Milano | 2744.982 | 2825.708 | +2.94% | 1 |
| AS Roma | 2006.060 | 2064.106 | +2.89% | 1 |
| FC Barcelona | 5238.805 | 5373.099 | +2.56% | 1 |

## Biggest club falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| SSC Napoli | 1796.360 | 1737.682 | -3.27% | 1 |
| Aston Villa FC | 1513.939 | 1468.665 | -2.99% | 1 |
| Fulham FC | 1719.016 | 1676.291 | -2.49% | 1 |
| US Lecce | 809.488 | 789.659 | -2.45% | 1 |
| Cagliari Calcio | 754.677 | 736.845 | -2.36% | 1 |
| FC Schalke 04 | 1030.902 | 1006.598 | -2.36% | 1 |
| Getafe CF | 592.348 | 578.775 | -2.29% | 1 |
| Olympique de Marseille | 2342.210 | 2289.955 | -2.23% | 1 |
| Real Club Celta de Vigo | 1283.640 | 1255.524 | -2.19% | 1 |
| Valencia CF | 929.105 | 909.812 | -2.08% | 1 |

## Biggest player rises

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Nicolò Barella | 2596.189 | 2661.306 | +2.51% | 1 |
| Bruno Fernandes | 6312.320 | 6461.418 | +2.36% | 1 |
| Ionut Radu | 948.512 | 970.349 | +2.30% | 1 |
| Youri Tielemans | 1853.162 | 1895.469 | +2.28% | 1 |
| Mario Hermoso | 1623.385 | 1658.592 | +2.17% | 1 |
| Kjell Scherpen | 981.452 | 1001.616 | +2.05% | 1 |
| Elia Caprile | 1057.237 | 1077.262 | +1.89% | 1 |
| Loris Karius | 997.006 | 1015.644 | +1.87% | 1 |
| Tarik Muharemovic | 1141.762 | 1162.620 | +1.83% | 1 |
| Lewis Ferguson | 1461.268 | 1487.674 | +1.81% | 1 |
| James Trafford | 1142.157 | 1162.721 | +1.80% | 1 |
| Lamine Yamal | 2586.552 | 2631.047 | +1.72% | 1 |
| Malick Junior Yalcouyé | 1014.610 | 1032.020 | +1.72% | 1 |
| Anton Kade | 1057.340 | 1074.203 | +1.59% | 1 |
| Jacobo Ramón | 1249.627 | 1269.528 | +1.59% | 1 |

## Biggest player falls

| Entity | Old | New | Change | Matches |
|---|---:|---:|---:|---:|
| Yéhvann Diouf | 1777.633 | 1742.127 | -2.00% | 1 |
| Bart Verbruggen | 1386.612 | 1363.364 | -1.68% | 1 |
| Dara O'Shea | 1048.599 | 1031.443 | -1.64% | 1 |
| Adama Camara | 1050.535 | 1034.733 | -1.50% | 1 |
| Yannik Engelhardt | 1120.607 | 1104.623 | -1.43% | 1 |
| Zion Suzuki | 1056.685 | 1041.746 | -1.41% | 1 |
| Lukasz Skorupski | 1215.377 | 1199.388 | -1.32% | 1 |
| Derry Scherhant | 1044.974 | 1032.330 | -1.21% | 1 |
| Karl Hein | 1084.230 | 1071.276 | -1.19% | 1 |
| Robin Fellhauer | 986.112 | 974.561 | -1.17% | 1 |
| Leif Davis | 863.614 | 853.823 | -1.13% | 1 |
| David Raya | 875.092 | 865.847 | -1.06% | 1 |
| Jesús Areso | 698.265 | 690.900 | -1.05% | 1 |
| Ferdi Kadioglu | 991.603 | 981.223 | -1.05% | 1 |
| Caoimhín Kelleher | 1179.530 | 1168.111 | -0.97% | 1 |

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
