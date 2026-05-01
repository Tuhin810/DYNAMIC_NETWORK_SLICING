# Research-Paper Style Summary

## Problem
The project studies how to allocate 5G devices across slices when traffic is mixed and conditions are uneven. The main challenge is to balance latency-sensitive emergency traffic, throughput-heavy video traffic, and lower-priority IoT traffic without relying only on static rules.

## Method
The repository compares three strategies:
- `static`: fixed assignment by device type
- `dynamic`: load-aware and priority-aware heuristic assignment
- `psdas`: Predictive SLA-Debt Aware Slicing

PSDAS is the novel method. It combines three ideas in one online policy:
- short-horizon load prediction using EWMA-style trend tracking
- SLA debt tracking per traffic-class and slice pair
- adaptive objective weighting over latency, throughput, and packet loss

The policy is designed to be ablated cleanly. The repository supports:
- no prediction
- no debt
- fixed weights

## Experimental Design
The evaluation uses deterministic scenario presets and repeated seeds. The scenarios are:
- balanced
- video_heavy
- emergency_burst
- high_congestion
- noisy_channel

The main evaluation protocol runs multiple seeds per scenario and compares the algorithms on:
- p95 and p99 latency
- SLA violation rate
- fairness index
- utility score
- throughput and packet-loss summaries

## Results
The Day 3 analysis shows that PSDAS is strongest where latency tails matter most.
- PSDAS consistently improves URLLC p95 latency in stressed scenarios.
- PSDAS also improves SLA compliance in several cases.
- Dynamic heuristics still win on some throughput-heavy outcomes, especially in eMBB-focused situations.

The ablation study indicates that SLA debt is the most important PSDAS component in the current implementation. Removing debt causes the largest utility drop, while removing prediction has smaller but still measurable impact.

## Interpretation
The main contribution is not a new simulator alone. The contribution is a reproducible research artifact that introduces a novel online slicing policy and then tests it with a full experiment pipeline, statistical analysis, and paper-ready outputs.

## Main Takeaway
PSDAS is a useful latency-aware and SLA-aware policy, but it is not uniformly best on every metric. That makes the result realistic and research-relevant: it improves some important QoS dimensions while exposing remaining trade-offs that future work can target.
