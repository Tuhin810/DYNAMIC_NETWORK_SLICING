# Algorithm Comparison

| Scenario | Algorithm | SLA Violation (%) | Fairness | Utility | URLLC p95 Latency (ms) |
|---|---:|---:|---:|---:|---:|
| balanced | dynamic | 100.000 | 0.8102 | 0.2665 | 18.834 |
| balanced | psdas | 98.889 | 0.8278 | 0.2813 | 21.499 |
| balanced | static | 81.667 | 0.6090 | 0.2427 | 8.348 |
| emergency_burst | dynamic | 100.000 | 0.8107 | 0.2542 | 22.653 |
| emergency_burst | psdas | 100.000 | 0.8092 | 0.2668 | 25.748 |
| emergency_burst | static | 73.889 | 0.6968 | 0.2421 | 11.449 |
| high_congestion | dynamic | 100.000 | 0.8570 | 0.1524 | 35.355 |
| high_congestion | psdas | 100.000 | 0.8002 | 0.1730 | 37.366 |
| high_congestion | static | 89.091 | 0.5636 | 0.1888 | 9.515 |
| noisy_channel | dynamic | 100.000 | 0.8315 | 0.2179 | 24.134 |
| noisy_channel | psdas | 100.000 | 0.8242 | 0.2376 | 27.199 |
| noisy_channel | static | 88.000 | 0.6838 | 0.2238 | 9.180 |
| video_heavy | dynamic | 100.000 | 0.8940 | 0.1813 | 35.355 |
| video_heavy | psdas | 100.000 | 0.8311 | 0.1915 | 36.929 |
| video_heavy | static | 79.444 | 0.5368 | 0.1845 | 8.783 |
