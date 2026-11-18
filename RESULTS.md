# Dharma Nanda: results

Scripted agents, 20 seeds per town, every town with the same cast: 6 honest sellers, 5 red-team sellers, 6 buyers, 5 judges (2 of them red team), 1 tester, 1 relay, 1 watchtower seat and a council of 3. Money is in cents. Good work is worth 1,600 to the buyer and costs 1,000; each judge is paid 40 for a verdict. Regenerate with `python run.py && python report.py > RESULTS.md`.

## Oversight, one actor at a time

| Town | Value delivered | Buyers' net (value − price − judge fees) | Paid for bad work | Good work refused | Honest sellers suspended (of 6) | Red sellers still trading (of 5) | Watchtower cases | Strikes taken back | Rule changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| No red team, no oversight | 140,000 ± 2,051 | 44,000 ± 2,051 | 8,500 ± 1,282 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Red team, no oversight | 92,000 ± 2,420 | -4,000 ± 2,420 | 38,500 ± 1,512 | 0.0 ± 0.0 | 0.0 ± 0.0 | 5.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Blue team | 115,760 ± 2,160 | 31,690 ± 852 | 200 ± 192 | 3.0 ± 0.4 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Blue team and watchtower | 115,920 ± 2,007 | 31,850 ± 729 | 100 ± 144 | 3.0 ± 0.4 | 2.8 ± 0.5 | 0.0 ± 0.0 | 2.7 ± 0.6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Blue team, watchtower and a slow council (reviews every 4 rounds, acts on 5 cases) | 115,920 ± 2,007 | 31,850 ± 729 | 100 ± 144 | 3.0 ± 0.4 | 2.8 ± 0.5 | 0.0 ± 0.0 | 2.7 ± 0.6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Blue team, watchtower and council (every 2 rounds, 3 cases) | 115,680 ± 2,171 | 31,760 ± 823 | 100 ± 144 | 2.7 ± 0.3 | 1.8 ± 0.7 | 0.0 ± 0.0 | 7.2 ± 1.8 | 2.1 ± 0.7 | 0.7 ± 0.2 |
| Blue team, watchtower and a fast council (every round, 2 cases) | 117,120 ± 2,231 | 32,300 ± 868 | 100 ± 144 | 2.0 ± 0.2 | 0.8 ± 0.5 | 0.0 ± 0.0 | 9.1 ± 1.3 | 1.9 ± 0.2 | 1.0 ± 0.0 |

## Records: the same blue-team town, three ways of checking a delivery on receipt

All deliveries start out through one relay. `No check` takes the bytes as they arrive. `NandaTown fingerprint` and `Canonical record (dataset.v1)` both look the arriving record up by its identity and ask for it once more if it is unknown; they differ only in how identity is computed. A relay whose delivery does not verify takes a strike, and at three strikes sellers switch to a second relay that passes bytes unchanged. In the last two rows there is no second relay. The two signature checks also require the seller's Ed25519 signature: over the bytes the record was published in, or over its canonical identity.

| Relay | Check on receipt | Value delivered | Good work refused because its record did not verify | Altered deliveries sent | Altered deliveries that reached the judges | Strikes on honest sellers for an answer the relay changed | Honest sellers suspended (of 6) | Altering relays suspended | Honest relays suspended | Parent links the audit could not resolve |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Relay passes bytes unchanged | No check | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay passes bytes unchanged | NandaTown fingerprint | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay passes bytes unchanged | Canonical record (dataset.v1) | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay passes bytes unchanged | Canonical record, signature over the identity | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | No check | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | NandaTown fingerprint | 114,800 ± 2,222 | 0.4 ± 0.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 1.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | Canonical record (dataset.v1) | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | Canonical record, signature over the bytes | 114,800 ± 2,222 | 0.4 ± 0.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 1.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record (same data, different bytes) | Canonical record, signature over the identity | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries | No check | 54,720 ± 5,368 | 0.0 ± 0.0 | 21.1 ± 1.1 | 21.1 ± 1.1 | 15.8 ± 1.2 | 6.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 57.0 ± 3.3 |
| Relay changes the answer in 30% of deliveries | NandaTown fingerprint | 114,960 ± 2,160 | 0.4 ± 0.3 | 3.4 ± 0.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.6 ± 0.4 | 1.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries | Canonical record (dataset.v1) | 114,960 ± 2,160 | 0.4 ± 0.3 | 3.4 ± 0.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.6 ± 0.4 | 1.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries | Canonical record, signature over the identity | 114,960 ± 2,160 | 0.4 ± 0.3 | 3.4 ± 0.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.6 ± 0.4 | 1.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries and publishes the result in the seller's name | No check | 54,720 ± 5,368 | 0.0 ± 0.0 | 21.1 ± 1.1 | 21.1 ± 1.1 | 15.8 ± 1.2 | 6.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries and publishes the result in the seller's name | NandaTown fingerprint | 54,720 ± 5,368 | 0.0 ± 0.0 | 21.1 ± 1.1 | 21.1 ± 1.1 | 15.8 ± 1.2 | 6.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries and publishes the result in the seller's name | Canonical record (dataset.v1) | 54,720 ± 5,368 | 0.0 ± 0.0 | 21.1 ± 1.1 | 21.1 ± 1.1 | 15.8 ± 1.2 | 6.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries and publishes the result in the seller's name | Canonical record, signature over the bytes | 114,960 ± 2,160 | 0.4 ± 0.3 | 3.4 ± 0.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.6 ± 0.4 | 1.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay changes the answer in 30% of deliveries and publishes the result in the seller's name | Canonical record, signature over the identity | 114,960 ± 2,160 | 0.4 ± 0.3 | 3.4 ± 0.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.6 ± 0.4 | 1.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record and is the only route | NandaTown fingerprint | 0 ± 0 | 68.7 ± 1.7 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 1.0 ± 0.0 | 0.0 ± 0.0 |
| Relay re-encodes every record and is the only route | Canonical record (dataset.v1) | 115,760 ± 2,160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |

## What is sent to the watchtower, and how good and how busy it is

No council in these towns. The watchtower is a stand-in policy, not a person: it decides rightly with the chance shown and takes the number of cases a round shown; a case over that number is held (refunded, no strike).

| Sent to the watchtower | Right | Cases a round | Buyers' net | Good work refused | Honest sellers suspended (of 6) | Red sellers still trading (of 5) | Cases | Cases held for lack of time | Cases decided rightly |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| No watchtower |  |  | 31,690 ± 852 | 3.0 ± 0.4 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Split panels only | 98% | 4 | 31,850 ± 729 | 3.0 ± 0.4 | 2.8 ± 0.5 | 0.0 ± 0.0 | 2.7 ± 0.6 | 0.0 ± 0.0 | 2.6 ± 0.6 |
| Split panels and flagged deliveries | 98% | 4 | 33,200 ± 720 | 0.1 ± 0.1 | 0.8 ± 0.4 | 0.0 ± 0.0 | 11.4 ± 1.3 | 0.0 ± 0.0 | 11.2 ± 1.2 |
| Split panels and flagged deliveries | 98% | 4 | 33,200 ± 720 | 0.1 ± 0.1 | 0.8 ± 0.4 | 0.0 ± 0.0 | 11.4 ± 1.3 | 0.0 ± 0.0 | 11.2 ± 1.2 |
| Split panels and flagged deliveries | 98% | 2 | 32,900 ± 785 | 0.2 ± 0.2 | 0.8 ± 0.4 | 0.0 ± 0.0 | 11.4 ± 1.3 | 0.7 ± 0.5 | 10.6 ± 1.0 |
| Split panels and flagged deliveries | 98% | 1 | 31,690 ± 901 | 1.4 ± 0.7 | 0.7 ± 0.4 | 0.0 ± 0.0 | 12.2 ± 1.5 | 3.5 ± 1.1 | 8.7 ± 0.8 |
| Split panels and flagged deliveries | 80% | 4 | 31,680 ± 955 | 1.2 ± 0.6 | 1.3 ± 0.6 | 0.0 ± 0.0 | 11.7 ± 1.4 | 0.0 ± 0.0 | 9.8 ± 1.3 |
| Split panels and flagged deliveries | 80% | 2 | 31,500 ± 1,058 | 1.4 ± 0.6 | 1.2 ± 0.5 | 0.0 ± 0.0 | 11.8 ± 1.4 | 0.8 ± 0.4 | 9.3 ± 1.0 |
| Split panels and flagged deliveries | 80% | 1 | 30,040 ± 1,222 | 2.5 ± 0.8 | 1.1 ± 0.5 | 0.0 ± 0.0 | 12.4 ± 1.6 | 3.7 ± 1.0 | 7.2 ± 0.9 |
| Split panels and flagged deliveries | 60% | 4 | 30,220 ± 1,185 | 2.1 ± 0.7 | 1.1 ± 0.6 | 0.0 ± 0.0 | 10.7 ± 1.3 | 0.0 ± 0.0 | 7.0 ± 1.3 |
| Split panels and flagged deliveries | 60% | 2 | 29,990 ± 1,246 | 2.5 ± 1.0 | 1.2 ± 0.6 | 0.0 ± 0.0 | 10.7 ± 1.5 | 0.6 ± 0.4 | 6.5 ± 1.2 |
| Split panels and flagged deliveries | 60% | 1 | 29,890 ± 1,249 | 2.7 ± 0.9 | 0.9 ± 0.5 | 0.0 ± 0.0 | 11.0 ± 1.6 | 3.0 ± 0.9 | 5.5 ± 1.1 |

## More red-team pressure

Each attack is added to the usual red team. `Watchtower` is sent split panels and flagged deliveries from the start; `Fast council` starts with flags refusing on their own and has to learn. A grinding buyer's own trades are left out of value and net; what it took is in its own column. In the three attacks the two judges who usually flag two honest sellers are doing the attack instead, so compare levels within an attack, not attacks with each other.

| Attack | Oversight | Value delivered | Buyers' net | Paid for bad work | Good work taken without paying | Good work refused | Honest sellers suspended (of 6) | Red sellers still trading (of 5) | Watchtower cases | Cases held for lack of time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| The usual red team | Blue team | 115,760 ± 2,160 | 31,690 ± 852 | 200 ± 192 | 0 ± 0 | 3.0 ± 0.4 | 2.7 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| The usual red team | Watchtower | 119,520 ± 1,817 | 33,200 ± 720 | 100 ± 144 | 0 ± 0 | 0.1 ± 0.1 | 0.8 ± 0.4 | 0.0 ± 0.0 | 11.4 ± 1.3 | 0.0 ± 0.0 |
| The usual red team | Fast council | 117,120 ± 2,231 | 32,300 ± 868 | 100 ± 144 | 0 ± 0 | 2.0 ± 0.2 | 0.8 ± 0.5 | 0.0 ± 0.0 | 9.1 ± 1.3 | 0.0 ± 0.0 |
| Two judges accept whatever red sellers deliver | Blue team | 112,720 ± 3,083 | 23,350 ± 2,633 | 7,400 ± 1,571 | 0 ± 0 | 0.0 ± 0.0 | 0.5 ± 0.3 | 0.3 ± 0.2 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Two judges accept whatever red sellers deliver | Watchtower | 119,440 ± 1,577 | 32,620 ± 717 | 650 ± 462 | 0 ± 0 | 0.0 ± 0.0 | 0.8 ± 0.4 | 0.0 ± 0.0 | 13.8 ± 0.7 | 0.1 ± 0.1 |
| Two judges accept whatever red sellers deliver | Fast council | 120,560 ± 1,990 | 32,940 ± 1,020 | 750 ± 452 | 0 ± 0 | 0.0 ± 0.0 | 0.7 ± 0.3 | 0.0 ± 0.0 | 13.1 ± 1.0 | 0.1 ± 0.1 |
| A buyer picks its own panel to get work refunded | Blue team | 90,800 ± 6,550 | 25,468 ± 2,086 | 50 ± 104 | 14,560 ± 1,082 | 9.1 ± 0.7 | 6.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| A buyer picks its own panel to get work refunded | Watchtower | 122,160 ± 2,227 | 34,290 ± 835 | 0 ± 0 | 240 ± 274 | 0.1 ± 0.2 | 1.4 ± 0.7 | 0.0 ± 0.0 | 20.1 ± 0.7 | 0.0 ± 0.0 |
| A buyer picks its own panel to get work refunded | Fast council | 121,760 ± 1,878 | 34,140 ± 704 | 0 ± 0 | 4,240 ± 439 | 2.6 ± 0.3 | 1.9 ± 0.6 | 0.0 ± 0.0 | 17.7 ± 0.8 | 0.0 ± 0.0 |
| Three of five judges flag every honest seller from round 6 | Blue team | 52,960 ± 2,461 | 12,128 ± 715 | 100 ± 144 | 0 ± 0 | 11.4 ± 1.2 | 6.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| Three of five judges flag every honest seller from round 6 | Watchtower | 113,280 ± 1,995 | 30,810 ± 789 | 150 ± 171 | 0 ± 0 | 4.1 ± 0.9 | 1.1 ± 0.4 | 0.1 ± 0.1 | 43.0 ± 1.1 | 3.8 ± 0.8 |
| Three of five judges flag every honest seller from round 6 | Fast council | 108,080 ± 2,584 | 28,910 ± 1,015 | 100 ± 144 | 0 ± 0 | 7.5 ± 1.0 | 1.9 ± 0.7 | 0.0 ± 0.0 | 38.8 ± 1.8 | 3.9 ± 0.9 |

