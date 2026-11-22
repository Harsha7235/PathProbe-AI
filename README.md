PATHPROBE AI — Topology-Aware Network Diagnosis & Path Recommendation
A Cisco Packet Tracer–integrated AI-assisted computer networking project
Built around a multi-site enterprise network topology, graph-based route analysis, fault-aware path ranking, and local LLM explanations.

PATHPROBE AI is a prototype developed inside Cisco Packet Tracer, using its Script Module and a custom interface. It is designed to inspect the network topology represented in Packet Tracer, discover candidate paths between selected endpoints, rank those paths using link-state and available metric information, and explain the recommendation with an optional locally hosted Ollama model.

This repository contains the Packet Tracer enterprise-network project and the PATHPROBE AI implementation/research documentation.
Table of contents
- Project overview
- Computer networks project
- What PATHPROBE AI does
- Architecture and workflow
- Path discovery and ranking
- Fault-injection laboratory
- AI-assisted explanation
- Implementation details
- How to open and explore
- Repository contents
- Research inspiration
- Current limitations and accuracy notes
- Future improvements
- Author
Project overview
Enterprise networks are made up of interconnected routers, switches, end devices, and communication links. A source and destination may have more than one possible route. The route with the fewest hops is not necessarily the healthiest route: it may contain a congested, unreliable, high-delay, or risky link.

PATHPROBE AI explores this problem through a topology-aware workflow:
1. Collect device and link information exposed by Cisco Packet Tracer.
2. Resolve link endpoints to their corresponding devices.
3. Represent the resolvable topology as a graph.
4. Discover a bounded set of candidate paths between a selected source and destination.
5. Rank candidates using a deterministic weighted penalty score.
6. Apply synthetic fault scenarios to study how route preference changes.
7. Optionally send the candidate-path context to a local Ollama-backed service for a human-readable explanation.
Core idea: use deterministic network/topology logic to discover and rank possible routes; use the language model as an explanation layer, not as the source of network topology truth.
Computer networks project
Multi-Site Enterprise Network
The Cisco Packet Tracer project, Multi-Site Enterprise Network.pkt, is the practical networking environment associated with this work. It represents a multi-site enterprise network for exploring network-device interconnection and end-to-end connectivity in a simulated enterprise setting.

Open the .pkt file in Cisco Packet Tracer to inspect the actual devices, links, addressing, and configurations present in the saved topology. The exact device inventory, IP plan, VLANs, routing protocols, and site configuration should be taken from the Packet Tracer file itself rather than inferred from the project title.
Networking concepts represented or explored
- Enterprise network topology and multi-site connectivity
- Routers, switches, end devices, and inter-device links
- Source-to-destination path selection
- Alternate candidate routes and hop count
- Link state and link availability
- Network performance considerations: delay, jitter, packet loss, bandwidth, throughput, utilization, and congestion
- Reliability and security-aware path considerations
- Fault scenarios and their effect on route preference
- Network troubleshooting and topology visibility
Important: The Packet Tracer topology is a simulated networking environment. PATHPROBE AI's generated fault metrics are synthetic what-if inputs; they are not live packet measurements from a production network.

What PATHPROBE AI does
Capability	Description
Topology inventory	Reads device and link records exposed through the Packet Tracer Script Module APIs.
Endpoint resolution	Maps link-port information to device records using identifiers and a connected-link UUID fallback.
Topology graph	Builds adjacency relationships from links whose endpoints can be resolved.
Candidate-path discovery	Searches for possible routes between a selected source and destination.
Weighted path ranking	Calculates a penalty score; a lower score is preferred.
Fault laboratory	Applies selectable synthetic fault conditions to links for what-if analysis.
RANDOM MIX	Applies a random combination of one to four fault features to a subset of links.
AI explanation	Optionally asks a local Ollama-backed analysis service to explain the supplied candidate paths and trade-offs.
Evidence awareness	Tracks unresolved endpoints and labels generated metrics as synthetic.


Architecture and workflow
Cisco Packet Tracer topology
          |
          v
Packet Tracer Script Module
  - device inventory
  - link / port inventory
  - link-state information where exposed
          |
          v
Endpoint resolver
  - identifier / UUID matching
  - connected-link UUID fallback
  - unresolved endpoint reporting
          |
          v
Topology snapshot handoff
  - cached snapshot
  - Script Engine / WebView bridge
          |
          v
Graph construction
  - vertices = represented devices
  - edges = resolvable links
          |
          v
Candidate-path enumerator
  - source and destination
  - bounded path search
          |
          v
Synthetic fault laboratory
  - baseline and fault scenarios
  - scenario-labelled metric overlays
          |
          v
Deterministic weighted scorer
  - link-state penalties
  - path metric penalties
  - lower score ranks higher
          |
          +--------------------------+
          |                          |
          v                          v
Ranked candidate paths        Optional local Ollama API
                              - explanation
                              - trade-offs
                              - recommendation
          |                          |
          +-------------+------------+
                        v
                 PATHPROBE AI interface
Main implementation components
- ScriptEngine.js — topology collection, endpoint resolution, snapshot caching/bridge, and device/link-state reporting.
- Interface0.htm — custom interface, synthetic fault scenarios, candidate-path enumeration, weighted scoring, and the Ollama analysis request.
The interface requests the cached topology snapshot through the Script Engine bridge ($se("requestSnapshot")). The implementation report records this handshake as an update intended to reduce a timing issue between snapshot delivery and WebView readiness. Successful end-to-end behaviour still needs to be checked in the relevant Packet Tracer runtime.
Path discovery and ranking
Graph model
The collected topology is represented as:
\[
G = (V,E)
\]
- \(V\): device nodes represented in the collected topology.
- \(E\): links whose two endpoints can be resolved.
- A candidate path is a sequence of adjacent nodes connecting source \(s\) to destination \(t\).
Only links with usable endpoint mappings can become graph edges. If endpoints remain unresolved, the graph may be incomplete and some routes may not be discovered.
Search bounds in the documented implementation
Search control	Value
Maximum candidate paths returned	12
Maximum hops per path	15
Maximum node expansions	20,000
Repeated nodes	Avoided within a path


These limits bound the search effort. They do not guarantee that every mathematically possible path is enumerated in every topology.
Weighted penalty scoring
The implementation uses a hand-coded heuristic score. Candidate paths are sorted in ascending order, so a lower score is preferred.
Factor	Penalty in the documented implementation
Hop count	\(10 \times\) number of hops
Explicitly down link	100,000 per link
Intermittent link	2,500 per link
Unknown link state	500 per link
Delay	\(1.5 \times\) delay in ms
Jitter	\(2 \times\) jitter in ms
Packet loss	\(25 \times\) loss percentage
Utilization	\(0.5 \times\) utilization percentage
Reliability	\(30 \times (99-\text{reliability})\), when reliability is below 99%
High security risk	+1,000
High queue congestion	+500
Trust	\(5 \times (100-\text{trust})\)
Throughput	\(100/\text{throughput in Mbps}\); +10,000 if throughput is non-positive


The score is a heuristic ranking function, not a trained machine-learning model, calibrated probability, SLA guarantee, or universally optimal routing algorithm. The weights are engineering choices and should be evaluated against repeatable scenarios.
Multi-metric path aggregation
The path-selection update describes the following aggregation rules when the corresponding per-link values are available:
- Total delay: \(D_{path} = \sum_i D_i\)
- Jitter estimate: \(J_{path} = \sum_i J_i\)
- End-to-end packet loss: \(P_{loss}=1-\prod_i(1-p_i)\), assuming independent per-link losses
- Bottleneck bandwidth: \(B_{path}=\min_i(B_i)\)
- Path reliability: \(R_{path}=\prod_i(R_i/100)\times100\), assuming independence
- Utilization: maximum link utilization as a conservative bottleneck indicator
- Trust/security: lowest trust and highest risk observed along the path
Missing metrics must not be fabricated or silently treated as healthy zero values. If path metrics are unavailable, the ranking is limited to the topology and link-state evidence that is actually available.
Fault-injection laboratory
The fault laboratory supports controlled what-if comparisons by applying synthetic changes to link attributes.
Scenario	What it represents
Normal baseline	Generated baseline values for supported metric fields
High latency / delay	Increased delay
High jitter	Increased delay variation
Packet loss	Increased packet-loss percentage
Burst packet loss	More severe loss and degraded stability/reliability
Queue congestion	High congestion and possible throughput degradation
High utilization	Increased utilization
Low bandwidth	Reduced available bandwidth
Low throughput	Reduced throughput relative to bandwidth
Low reliability	Reduced reliability percentage
Security risk	High risk and reduced trust
Trust degradation	Lower trust and potentially elevated risk
Simulated link failure	Marks a link as simulated down for ranking
Intermittent link	Marks a link intermittent
Combined stress	Combines multiple fault families
RANDOM MIX	Randomly combines one to four distinct fault features


In the documented implementation, RANDOM MIX applies to 60% of links, while other selected scenarios apply to 35% of links. These are simulation design settings, not real-world fault rates.

A simulated link failure does not physically disable the Packet Tracer link or change actual router routing. The fault laboratory is intended to demonstrate how the candidate ranking responds to altered inputs.
Suggested demonstration sequence
1. Run a baseline comparison between available candidate paths.
2. Apply delay, congestion, and packet-loss stress to a shorter route.
3. Recalculate candidate paths and compare the scores.
4. Check whether a longer but healthier eligible route ranks higher.
5. Apply a simulated failure and inspect the penalty or availability outcome.
6. Test security-risk/trust conditions.
7. Check that unavailable metrics remain labelled unknown rather than being assumed healthy.
The outcome should be recorded from the actual Packet Tracer session before publishing experimental claims.
AI-assisted explanation
PATHPROBE AI can send candidate-path context to a local analysis endpoint:
http://127.0.0.1:8000/api/analyze
The documented task name is rank_network_candidate_paths. The request includes the candidate-path context, simulation status, selected scenario, and an explicit synthetic-metrics indicator.

The local Ollama-backed model is asked to:
- Choose among the supplied candidate paths.
- Explain the ranking and relevant trade-offs.
- Consider delay, jitter, packet loss, utilization, bandwidth, throughput, reliability, trust, security risk, and link state when supplied.
- Use the provided candidate values.
- Avoid inventing missing measurements.
- Avoid claiming that Packet Tracer routing or device configuration was changed.
Division of responsibility:
- Graph search discovers candidate paths.
- Deterministic scoring calculates the numerical ranking.
- Ollama provides a natural-language explanation of the supplied evidence.
The LLM does not replace graph search or the scorer. Its availability depends on the local service and model being configured and running.
Implementation details
Technologies and environment documented
- Cisco Packet Tracer 9.0.0.0810
- Packet Tracer Script Module APIs
- JavaScript (ScriptEngine.js)
- HTML / JavaScript custom interface (Interface0.htm)
- Local Ollama-backed analysis service
- HTTP analysis endpoint at 127.0.0.1:8000/api/analyze
Endpoint resolution
The documented resolver:
1. Builds device/port lookup structures from the collected inventory.
2. Attempts endpoint matching using identifiers exposed by the port and associated device.
3. Uses a connected-link UUID fallback when required.
4. Counts unresolved endpoints rather than silently inventing a device mapping.
5. Exposes a partial-topology warning when unresolved endpoints remain.
An earlier development observation reported 75 devices, 110 links, and 36 unresolved endpoints for one topology/session. These are historical observations, not universal results and not a claim about the current .pkt file. The updated fallback requires runtime verification on the chosen topology.
How to open and explore
1. Install/open a compatible version of Cisco Packet Tracer.
2. Open Multi-Site Enterprise Network.pkt.
3. Inspect the actual topology, devices, links, addressing, and device configurations.
4. Open the PATHPROBE AI Script Module/interface implementation in the Packet Tracer project environment.
5. Allow the Script Engine to collect the topology snapshot.
6. Select source and destination endpoints in the interface.
7. Inspect discovered candidate paths and their ranking.
8. Select a fault scenario and run the analysis again to compare the ranking.
9. If using AI explanation, start and configure the local Ollama analysis service and the API expected by the interface.
The exact installation and launch procedure can depend on how the Script Module and local API are packaged in the working environment. The report documents the endpoint but does not establish that every installation has a configured backend.
Repository contents
Suggested repository layout:
.
├── README.md
├── Multi-Site Enterprise Network.pkt
├── PATHPROBE_AI_Implementation_and_Literature_Comparison.docx
└── PATHPROBE_AI_Metric_Aware_Path_Selection_Update.docx
If you are publishing the implementation source as well, include the relevant Script Module and interface files:
├── ScriptEngine.js
└── Interface0.htm
Only include source files that you are permitted to share and that are actually part of the project.
Research inspiration
The implementation report positions the project alongside research on reliable LLM-based network management, LLMs for networking operations, semantic network diagnosis, digital-twin-based fault diagnosis, and graph-neural-network fault diagnosis.

The report discusses these works as research inspirations, not as algorithms reproduced by PATHPROBE AI:
1. MeshAgent: Enabling Reliable Network Management with Large Language Models (2025), DOI: 10.1145/3771567
2. Large Language Models for Computer Networking Operations and Management: A Survey (2025), DOI: 10.1016/j.comnet.2025.111614
3. NetSemantic: Adapting Network Information to Semantics for Generalizable and Plug-and-Play Multi-Scenario Network Diagnosis (2025), arXiv: 2501.16842
4. Semi-Distributed Network Fault Diagnosis Based on Digital Twin Network in Highly Dynamic Heterogeneous Networks (2025), DOI: 10.1109/TMC.2024.3519576
5. A Graph Neural Network Approach for Hybrid Node-Edge Fault Diagnosis in Interconnection Networks Under the HPMC Model* (2026), DOI: 10.1109/TON.2026.3670807
PATHPROBE AI does not currently implement the papers' invariant-extraction workflow, semantic knowledge-graph update method, FTS-LSTM, GraphSAGE/Hybrid-GNN, or their published evaluation pipelines.
Current limitations and accuracy notes
Please keep these boundaries clear when describing or demonstrating the project:
- Performance metrics produced by the fault lab are synthetic unless a separately measured source is integrated.
- The current implementation does not establish live delay, jitter, packet-loss, throughput, utilization, or reliability telemetry from real packet flows.
- Security-risk and trust values are simulated attributes; they are not packet inspection, an intrusion-detection engine, cryptographic trust, or a verified security assessment.
- Endpoint resolution can be incomplete depending on the topology and Script Module API data.
- Candidate-path search is bounded and may not enumerate every possible route.
- The weighted score uses hand-coded heuristic constants; it has not been calibrated against a labelled dataset.
- No trained ML model, GNN classifier, or ML training dataset is evidenced in the documented implementation.
- Ollama explanations depend on a functioning local service and should be checked against the supplied path evidence.
- The tool recommends and explains routes; it does not automatically change router/switch configuration or Packet Tracer routing.
- The literature comparison is conceptual; no formal benchmark against the cited papers is claimed.
- Syntax checks do not prove successful end-to-end runtime operation on every Packet Tracer topology.
Future improvements
- Verify topology collection and endpoint resolution across multiple Packet Tracer topologies.
- Record resolved/unresolved endpoint counts and collection time.
- Validate discovered candidate paths against manually inspected routes.
- Compare multi-metric ranking with fewest-hop and link-state-only baselines.
- Record ranking changes before and after each fault scenario.
- Evaluate AI explanations for evidence use, trade-off accuracy, and correct synthetic-data labelling.
- Test repeatability across random seeds and RANDOM MIX scenarios.
- Integrate independently measured telemetry only with clear source, timestamp, and provenance.
- Consider approved, auditable remediation workflows only as a separate future development.
Author
P.Harsha Vardhan Reddy
B.Tech — Artificial Intelligence & Data Science(CPS&S)
Amrita Vishwa Vidyapeetham, Coimbatore
Project status: Packet Tracer-integrated prototype. Feature descriptions and implementation boundaries are based on the accompanying PATHPROBE AI implementation report and multi-metric path-selection update. Validate runtime behaviour in Packet Tracer before claiming measured results.
