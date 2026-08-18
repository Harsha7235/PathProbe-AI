# PathProbe-Agent Research Design

## 1. Research Problem

Network paths may contain hidden traffic-management mechanisms,
middleboxes, filtering policies, MTU restrictions, or QoS-dependent
treatment.

Traditional measurement approaches often use a predefined set of
probes and collect measurements for later analysis.

PathProbe-Agent investigates whether an autonomous agent can
adaptively select network probes based on observations and
progressively characterize an unknown network path.

---

## 2. Core Research Question

Can an autonomous probing agent identify hidden network-path
behaviors using fewer measurements than a fixed exhaustive probing
strategy?

---

## 3. Secondary Research Questions

1. Can the agent identify previously unseen combinations of
   network behaviors?

2. Can the agent generalize across different network topologies?

3. How many probes are required before the agent reaches a reliable
   diagnosis?

4. Can every diagnosis be supported by measured experimental
   evidence?

---

## 4. Probe Space

The initial probe toolbox contains:

- P1: Baseline probe
- P2: Packet-size sweep
- P3: Rate sweep
- P4: DSCP variation
- P5: TTL variation

---

## 5. Hidden Network Environments

The simulation environment will contain:

- E0: Normal
- E1: Rate limiting
- E2: MTU limitation
- E3: Selective filtering
- E4: DSCP-dependent treatment
- E5: Combined behavior

The agent does not receive the environment label during
investigation.

---

## 6. Fixed Baseline

The fixed strategy executes all available probes:

P1 → P2 → P3 → P4 → P5

The resulting measurements are used to produce a diagnosis.

This provides the baseline against which adaptive probing is evaluated.

---

## 7. Adaptive Agent

The agent begins with uncertainty about the network path.

The investigation loop is:

Observe
→ Form hypothesis
→ Select next probe
→ Execute probe
→ Measure response
→ Update hypothesis
→ Stop or select another probe

---

## 8. Agent Constraints

The agent cannot directly modify the network.

All measurements must originate from the probe executor.

The agent can only request probes from the approved probe toolbox.

---

## 9. Evaluation Metrics

The system will be evaluated using:

- Diagnosis accuracy
- Number of probes
- Measurement cost
- Investigation time
- False diagnosis rate
- Confidence at termination
- Unseen-combination performance
- Cross-topology performance

---

## 10. Main Comparison

Two approaches will be compared:

### Fixed probing

P1 + P2 + P3 + P4 + P5

### Adaptive probing

The agent selects only the probes required to reach a reliable
diagnosis.

The primary research metric is the trade-off between diagnosis
accuracy and probing cost.

---

## 11. Expected Contribution

The project aims to demonstrate an evidence-grounded autonomous
network-path investigation system rather than a conventional
post-hoc network traffic classifier.