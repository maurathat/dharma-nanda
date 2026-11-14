# Dharma Nanda: results

Scripted agents, 20 seeds per town, every town with the same cast: 6 honest sellers, 5 red-team sellers, 6 buyers, 5 judges (2 of them red team), 1 tester, 1 relay, 1 watchtower seat and a council of 3. Money is in cents. Good work is worth 1,600 to the buyer and costs 1,000; each judge is paid 40 for a verdict. Regenerate with `python run.py && python report.py > RESULTS.md`.

## Oversight, one actor at a time

| Town | Value delivered | Buyers' net (value − price − judge fees) | Paid for bad work | Good work refused | Honest sellers suspended (of 6) | Red sellers still trading (of 5) | Watchtower cases | Strikes taken back | Rule changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| No red team, no oversight | 140,000 ± 2,051 | 44,000 ± 2,051 | 8,500 ± 1,282 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Red team, no oversight | 92,000 ± 2,420 | -4,000 ± 2,420 | 38,500 ± 1,512 | 0.0 ± 0.0 | 0.0 ± 0.0 | 5.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Blue team | 115,760 ± 2,160 | 31,690 ± 852 | 200 ± 192 | 3.0 ± 0.4 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Blue team and watchtower | 115,920 ± 2,007 | 31,850 ± 729 | 100 ± 144 | 3.0 ± 0.4 | 2.8 ± 0.5 | 0.0 ± 0.0 | 2.7 ± 0.6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Blue team, watchtower and council | 115,680 ± 2,171 | 31,760 ± 823 | 100 ± 144 | 2.7 ± 0.3 | 1.8 ± 0.7 | 0.0 ± 0.0 | 7.2 ± 1.8 | 2.1 ± 0.7 | 0.7 ± 0.2 |

## Records: the same blue-team town, three ways of checking a delivery on receipt

All deliveries pass through one relay. `No check` takes the bytes as they arrive. `NandaTown fingerprint` and `Canonical record (dataset.v1)` both look the arriving record up by its identity and ask for it once more if it is unknown; they differ only in how identity is computed.

| Relay | Check on receipt | Value delivered | Good work refused because its record did not verify | Altered deliveries sent | Altered deliveries that reached the judges | Strikes on honest sellers for an answer the relay changed | Honest sellers suspended (of 6) | Parent links the audit could not resolve |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Relay passes bytes unchanged | No check | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 |
| Relay passes bytes unchanged | NandaTown fingerprint | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 |
| Relay passes bytes unchanged | Canonical record (dataset.v1) | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | No check | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | NandaTown fingerprint | 0 ± 0 | 68.7 ± 1.7 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | Canonical record (dataset.v1) | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries | No check | 54,720 ± 5,368 | 0.0 ± 0.0 | 21.1 ± 1.1 | 21.1 ± 1.1 | 15.8 ± 1.2 | 6.0 ± 0.0 | 57.0 ± 3.3 |
| Relay changes the answer in 30% of deliveries | NandaTown fingerprint | 104,320 ± 2,095 | 7.5 ± 1.2 | 41.5 ± 2.7 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.5 ± 0.4 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries | Canonical record (dataset.v1) | 104,320 ± 2,095 | 7.5 ± 1.2 | 41.5 ± 2.7 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.5 ± 0.4 | 0.0 ± 0.0 |

