# PATHPROBE-AI

## Final Project Evaluation

Generated: 2026-08-19T05:48:58.478114

---

## 1. Project Objective

PathProbe-AI is an autonomous network-path diagnosis system combining:

- ns-3 network simulation
- active network probing
- deterministic evidence analysis
- grounded Qwen LLM reasoning
- adaptive probe selection
- autonomous investigation
- robustness evaluation
- persistent experiment reporting

The system diagnoses three hidden network behaviors:

1. NORMAL
2. RATE_LIMITED
3. DELAY

---

## 2. System Pipeline

```text
Hidden ns-3 Environment
        |
        v
Active Network Probe
        |
        v
Packet Loss / Delay / Throughput
        |
        v
Deterministic Evidence Engine
        |
        v
Grounded Qwen Reasoning
        |
        v
Adaptive Probe Selection
        |
        v
Autonomous Diagnosis
        |
        v
Investigation Report
        |
        v
Evaluation
```

---

## 3. Adaptive vs Fixed Evaluation

| Metric | Result |
|---|---:|
| Adaptive Accuracy | 100.00% |
| Fixed Accuracy | 100.00% |
| Adaptive Average Probes | 2.67 |
| Fixed Average Probes | 4.00 |
| Probe Reduction | 33.33% |

The adaptive agent maintains diagnosis accuracy while reducing the number of required probes.

---

## 4. Robustness Evaluation

| Metric | Result |
|---|---:|
| Total Runs | 9 |
| Passed Runs | 9 |
| Robustness Accuracy | 100.00% |

---

## 5. Perturbation Evaluation

| Metric | Result |
|---|---:|
| Total Tests | 3 |
| Passed Tests | 3 |
| Perturbation Accuracy | 100.00% |

---

## 6. End-to-End Evaluation

| Metric | Result |
|---|---:|
| Total Tests | 3 |
| Passed Tests | 3 |
| End-to-End Accuracy | 100.00% |

---

## 7. Overall Evaluation

**Overall evaluation accuracy: 100.00%**

---

## 8. Network Signatures

### NORMAL

- Low delay
- Zero packet loss
- Throughput increases with offered load
- No congestion signature

### RATE_LIMITED

- Initially normal behavior
- Increasing load produces packet loss
- Delay increases sharply
- Throughput approaches saturation

### DELAY

- Persistent high delay
- Little or no packet loss
- Delay remains high across probe rates

---

## 9. Main Contribution

**black-box active probing + deterministic evidence + grounded local LLM reasoning + autonomous probe selection**

The hidden environment label is not provided to the LLM. The reasoning engine receives network measurements and determines the most likely network condition.

---

## 10. Limitations

The current evaluation uses three controlled ns-3 environments:

- E0 NORMAL
- E1 RATE_LIMITED
- E2 DELAY

Future work can include:

- additional failure classes
- jitter
- packet corruption
- routing failures
- wireless networks
- real network traces
- larger network topologies
- additional LLMs
- real-world deployment

---

## 11. Conclusion

PathProbe-AI demonstrates a closed-loop autonomous network diagnosis workflow.

The system observes a network path, analyzes measured behavior, reasons about competing hypotheses, selects additional probes when necessary, and terminates when sufficient evidence supports a diagnosis.

The evaluation framework measures diagnosis accuracy, probing efficiency, robustness, perturbation tolerance, and complete end-to-end operation.
