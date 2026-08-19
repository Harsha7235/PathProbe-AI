
import json
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path


# ============================================================
# PATHPROBE-AI
# HYBRID AUTONOMOUS NETWORK DIAGNOSIS AGENT
# ============================================================

# ------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------
# REPORTING MODULES
# ------------------------------------------------------------

from reports.investigation_report import generate_report
from reports.investigation_results import save_investigation_result


# ============================================================
# NS-3 CONFIGURATION
# ============================================================

NS3_DIR = Path("/home/harsha/ns-3.48")


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

# Windows Ollama exposed to WSL.
OLLAMA_URL = "http://172.20.192.1:11434/api/generate"

MODEL = "qwen3:8b"


# ============================================================
# NS-3 ENVIRONMENTS
# ============================================================

PROBES = {

    "E0":
        NS3_DIR /
        "build/scratch/ns3.48-pathprobe_rate-default",

    "E1":
        NS3_DIR /
        "build/scratch/ns3.48-pathprobe_rate_limited-default",

    "E2":
        NS3_DIR /
        "build/scratch/ns3.48-pathprobe_delay_jitter-default"
}


# ============================================================
# AVAILABLE PROBE RATES
# ============================================================

PROBE_RATES = [
    50,
    100,
    200,
    500
]


# ============================================================
# MAXIMUM PROBE BUDGET
# ============================================================

MAX_PROBES = 4


# ============================================================
# DETERMINISTIC EVIDENCE ENGINE
# ============================================================

def calculate_evidence(observations):

    if not observations:

        return {

            "classification":
                "UNCERTAIN",

            "signals":
                [],

            "recommendation":
                "Need initial measurement."
        }


    latest = observations[-1]

    loss = latest[
        "packet_loss_percent"
    ]

    delay = latest[
        "average_delay_ms"
    ]


    signals = []


    # ========================================================
    # CURRENT LOSS
    # ========================================================

    if loss == 0:

        signals.append(
            "No packet loss observed at "
            "the current probe rate."
        )

    else:

        signals.append(
            f"Packet loss detected: "
            f"{loss:.2f}%."
        )


    # ========================================================
    # CURRENT DELAY
    # ========================================================

    if delay < 50:

        signals.append(
            f"Low delay detected: "
            f"{delay:.1f} ms."
        )

    elif delay >= 100:

        signals.append(
            f"High delay detected: "
            f"{delay:.1f} ms."
        )

    else:

        signals.append(
            f"Moderate delay detected: "
            f"{delay:.1f} ms."
        )


    # ========================================================
    # CONSECUTIVE MEASUREMENT COMPARISON
    # ========================================================

    if len(observations) >= 2:

        previous = observations[-2]

        previous_loss = previous[
            "packet_loss_percent"
        ]

        previous_delay = previous[
            "average_delay_ms"
        ]


        loss_change = (
            loss -
            previous_loss
        )

        delay_change = (
            delay -
            previous_delay
        )


        if loss_change > 5:

            signals.append(

                f"Packet loss increased by "
                f"{loss_change:.2f} "
                f"percentage points."
            )


        if delay_change > 50:

            signals.append(

                f"Delay increased sharply by "
                f"{delay_change:.1f} ms."
            )


    # ========================================================
    # PERSISTENT HIGH DELAY
    # ========================================================

    high_delay_zero_loss = [

        obs

        for obs in observations

        if (

            obs[
                "average_delay_ms"
            ] >= 100

            and

            obs[
                "packet_loss_percent"
            ] == 0
        )
    ]


    persistent_delay = False


    if len(high_delay_zero_loss) >= 2:

        delays = [

            obs[
                "average_delay_ms"
            ]

            for obs
            in high_delay_zero_loss
        ]


        if (
            max(delays) -
            min(delays)
            <= 10
        ):

            persistent_delay = True


            signals.append(

                "Persistent high-delay "
                "signature detected: delay "
                "remains around the same high "
                "level while packet loss "
                "remains zero."
            )


    # ========================================================
    # RATE-LIMIT / CONGESTION SIGNATURE
    # ========================================================

    congestion_signature = False


    for obs in observations:

        if (

            obs[
                "packet_loss_percent"
            ] > 5

            and

            obs[
                "average_delay_ms"
            ] >= 100
        ):

            congestion_signature = True


            signals.append(

                "Congestion signature detected: "
                "packet loss and high delay "
                "occur under increased "
                "offered load."
            )


            break


    # ========================================================
    # FINAL CLASSIFICATION
    # ========================================================

    if congestion_signature:

        classification = (
            "RATE_LIMITED"
        )


    elif persistent_delay:

        classification = (
            "DELAY"
        )


    elif (

        len(observations) >= 2

        and

        latest[
            "packet_loss_percent"
        ] == 0

        and

        latest[
            "average_delay_ms"
        ] < 50

        and

        latest[
            "probe_rate_pps"
        ] >= 200
    ):

        classification = (
            "NORMAL"
        )


    else:

        classification = (
            "UNCERTAIN"
        )


    return {

        "classification":
            classification,

        "signals":
            signals,

        "recommendation":
            classification
    }


# ============================================================
# AUTONOMOUS PATHPROBE AGENT
# ============================================================

class AutonomousPathProbe:

    def __init__(self):

        self.observations = []

        self.history = []


    # ========================================================
    # RUN NS-3
    # ========================================================

    def run_ns3(
        self,
        environment,
        rate
    ):

        executable = PROBES[
            environment
        ]


        if not executable.exists():

            raise FileNotFoundError(

                "\nns-3 executable not found:\n"
                f"{executable}\n"
            )


        command = [

            str(executable),

            f"--packetsPerSecond={rate}"
        ]


        # ----------------------------------------------------
        # E1 HIDDEN RATE LIMIT
        # ----------------------------------------------------

        if environment == "E1":

            command.append(
                "--rateLimit=1Mbps"
            )


        # ----------------------------------------------------
        # EXECUTE NS-3
        # ----------------------------------------------------

        result = subprocess.run(

            command,

            cwd=NS3_DIR,

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace"
        )


        if result.returncode != 0:

            print(
                result.stdout
            )

            print(
                result.stderr
            )

            raise RuntimeError(
                "ns-3 execution failed."
            )


        output = result.stdout


        # ====================================================
        # PARSE NS-3 OUTPUT
        # ====================================================

        loss_match = re.search(

            r"Packet Loss\s*:\s*([\d.]+)",

            output
        )


        delay_match = re.search(

            r"Average Delay\s*:\s*([\d.]+)",

            output
        )


        throughput_match = re.search(

            r"Throughput\s*:\s*([\d.]+)",

            output
        )


        sent_match = re.search(

            r"Packets Sent\s*:\s*(\d+)",

            output
        )


        received_match = re.search(

            r"Packets Received\s*:\s*(\d+)",

            output
        )


        if not all([

            loss_match,

            delay_match,

            throughput_match,

            sent_match,

            received_match

        ]):

            print(output)

            raise RuntimeError(

                "Could not parse ns-3 output."
            )


        # ====================================================
        # BLACK-BOX OBSERVATION
        # ====================================================

        observation = {

            "probe_rate_pps":
                rate,

            "packets_sent":
                int(
                    sent_match.group(1)
                ),

            "packets_received":
                int(
                    received_match.group(1)
                ),

            "packet_loss_percent":
                float(
                    loss_match.group(1)
                ),

            "throughput_mbps":
                float(
                    throughput_match.group(1)
                ),

            "average_delay_ms":
                float(
                    delay_match.group(1)
                )
        }


        return observation


    # ========================================================
    # BUILD GROUNDED QWEN PROMPT
    # ========================================================

    def build_prompt(self):

        evidence = calculate_evidence(
            self.observations
        )


        measurements = json.dumps(

            self.observations,

            indent=2
        )


        derived_evidence = json.dumps(

            evidence,

            indent=2
        )


        return f"""
You are the autonomous reasoning engine
of PathProbe-AI.

You are diagnosing an UNKNOWN network path.

You do NOT know which hidden environment
generated the measurements.

Possible diagnoses:

NORMAL
RATE_LIMITED
DELAY


------------------------------------------------------------
DIAGNOSTIC DEFINITIONS
------------------------------------------------------------

NORMAL:

Low delay, normally below 50 ms,
with zero or negligible packet loss.


RATE_LIMITED:

The network initially behaves normally
at low load, but increasing offered traffic
causes:

- packet loss
- severe queueing delay
- throughput saturation
- sudden degradation

A low-rate observation alone is NOT
sufficient to rule out RATE_LIMITED.


DELAY:

Persistent high delay, approximately
100 ms or more, with little or no
packet loss.


------------------------------------------------------------
IMPORTANT AGENT RULES
------------------------------------------------------------

1. Never invent measurements.

2. Never use hidden environment names.

3. A 50 or 100 pps measurement showing
   low delay and zero loss is NOT sufficient
   to declare NORMAL.

4. If the path still looks normal at low
   load, actively probe a higher rate.

5. NORMAL should only be confirmed after
   a higher-load probe of at least 200 pps
   still shows low delay and zero packet loss.

6. If packet loss and severe delay appear
   when offered load increases, strongly
   consider RATE_LIMITED.

7. If delay remains >=100 ms across
   multiple probes while packet loss
   remains zero, strongly consider DELAY.

8. Use ONLY the supplied measurements.

9. Do not invent evidence.

10. Do not mention or infer hidden labels.


------------------------------------------------------------
DETERMINISTIC EVIDENCE ENGINE
------------------------------------------------------------

{derived_evidence}


------------------------------------------------------------
RAW MEASUREMENTS
------------------------------------------------------------

{measurements}


------------------------------------------------------------
YOUR TASK
------------------------------------------------------------

Reason over the evidence and decide:

- current hypothesis
- confidence
- measured evidence
- whether another probe is needed
- next probe rate

Available probe rates:

50
100
200
500


Return ONLY valid JSON.

Required format:

{{
    "hypothesis":
        "NORMAL | RATE_LIMITED | DELAY",

    "confidence":
        0.0,

    "reasoning":
        "brief explanation",

    "evidence":
        [
            "specific measured evidence"
        ],

    "next_probe_rate_pps":
        50,

    "stop":
        false
}}
"""


    # ========================================================
    # ASK QWEN
    # ========================================================

    def ask_llm(self):

        prompt = self.build_prompt()


        payload = {

            "model":
                MODEL,

            "prompt":
                prompt,

            "stream":
                False,

            "format":
                "json"
        }


        data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )


        request = urllib.request.Request(

            OLLAMA_URL,

            data=data,

            headers={

                "Content-Type":
                    "application/json"
            },

            method="POST"
        )


        try:

            with urllib.request.urlopen(

                request,

                timeout=180

            ) as response:

                result = json.loads(

                    response.read()
                )


        except urllib.error.URLError as error:

            raise RuntimeError(

                "\nCould not connect to Ollama.\n"
                "Make sure Windows Ollama is running "
                "and accessible from WSL.\n\n"
                f"Original error: {error}\n"
            )


        response_text = result.get(

            "response",

            ""
        )


        if not response_text:

            raise RuntimeError(

                "Ollama returned an empty response."
            )


        try:

            decision = json.loads(

                response_text
            )


        except json.JSONDecodeError:

            print()

            print(
                "RAW QWEN RESPONSE"
            )

            print(
                "----------------------------------------"
            )

            print(
                response_text
            )

            print(
                "----------------------------------------"
            )

            raise RuntimeError(

                "Qwen did not return valid JSON."
            )


        return decision


    # ========================================================
    # SAFETY / DECISION POLICY
    # ========================================================

    def enforce_decision(
        self,
        decision
    ):

        evidence = calculate_evidence(

            self.observations
        )


        classification = evidence[
            "classification"
        ]


        used_rates = {

            obs[
                "probe_rate_pps"
            ]

            for obs
            in self.observations
        }


        latest_rate = self.observations[-1][
            "probe_rate_pps"
        ]


        # ====================================================
        # RATE LIMITED
        # ====================================================

        if classification == "RATE_LIMITED":

            decision[
                "hypothesis"
            ] = "RATE_LIMITED"


            decision[
                "confidence"
            ] = max(

                float(

                    decision.get(

                        "confidence",

                        0.0
                    )
                ),

                0.90
            )


            decision[
                "reasoning"
            ] = (

                "Increasing offered load produced "
                "packet loss together with severe "
                "delay, indicating a congestion or "
                "rate-limiting signature."
            )


            decision[
                "evidence"
            ] = evidence[
                "signals"
            ]


            decision[
                "stop"
            ] = True


            return decision


        # ====================================================
        # DELAY
        # ====================================================

        if classification == "DELAY":

            decision[
                "hypothesis"
            ] = "DELAY"


            decision[
                "confidence"
            ] = max(

                float(

                    decision.get(

                        "confidence",

                        0.0
                    )
                ),

                0.90
            )


            decision[
                "reasoning"
            ] = (

                "Persistent high delay of approximately "
                "100 ms or greater is observed across "
                "multiple probes while packet loss "
                "remains zero."
            )


            decision[
                "evidence"
            ] = evidence[
                "signals"
            ]


            decision[
                "stop"
            ] = True


            return decision


        # ====================================================
        # NORMAL
        # ====================================================

        if classification == "NORMAL":

            decision[
                "hypothesis"
            ] = "NORMAL"


            decision[
                "confidence"
            ] = max(

                float(

                    decision.get(

                        "confidence",

                        0.0
                    )
                ),

                0.90
            )


            decision[
                "reasoning"
            ] = (

                "Multiple probes including a "
                "higher-load probe show low delay "
                "below 50 ms and zero packet loss. "
                "No congestion or saturation "
                "signature was observed."
            )


            decision[
                "evidence"
            ] = evidence[
                "signals"
            ]


            decision[
                "stop"
            ] = True


            return decision


        # ====================================================
        # NOT ENOUGH EVIDENCE
        # ====================================================

        decision[
            "stop"
        ] = False


        higher_rates = sorted(

            [

                rate

                for rate
                in PROBE_RATES

                if (

                    rate > latest_rate

                    and

                    rate not in used_rates
                )
            ]
        )


        if higher_rates:

            decision[
                "next_probe_rate_pps"
            ] = higher_rates[0]


        else:

            remaining_rates = [

                rate

                for rate
                in PROBE_RATES

                if rate not in used_rates
            ]


            if remaining_rates:

                decision[
                    "next_probe_rate_pps"
                ] = remaining_rates[0]

            else:

                decision[
                    "next_probe_rate_pps"
                ] = None


        return decision


    # ========================================================
    # DISPLAY AGENT STATE
    # ========================================================

    def print_state(

        self,

        step,

        observation,

        decision
    ):

        evidence = calculate_evidence(

            self.observations
        )


        print()

        print(
            "========================================"
        )

        print(

            f"       PATHPROBE-AI AGENT STEP {step}"
        )

        print(
            "========================================"
        )


        print(

            f"Probe Rate       : "
            f"{observation['probe_rate_pps']} pps"
        )


        print(

            f"Packet Loss      : "
            f"{observation['packet_loss_percent']} %"
        )


        print(

            f"Average Delay    : "
            f"{observation['average_delay_ms']} ms"
        )


        print(

            f"Throughput       : "
            f"{observation['throughput_mbps']} Mbps"
        )


        print()


        print(

            f"Evidence Engine  : "
            f"{evidence['classification']}"
        )


        print()


        print(

            f"Qwen Hypothesis  : "
            f"{decision.get('hypothesis')}"
        )


        print(

            f"Confidence       : "
            f"{decision.get('confidence')}"
        )


        print(

            f"Reasoning        : "
            f"{decision.get('reasoning')}"
        )


        print()

        print("Evidence:")


        for item in decision.get(

            "evidence",

            []

        ):

            print(
                f"  - {item}"
            )


        print()


        print(

            f"Next Probe       : "
            f"{decision.get('next_probe_rate_pps')} pps"
        )


        print(

            f"Stop             : "
            f"{decision.get('stop')}"
        )


        print(
            "========================================"
        )


    # ========================================================
    # GENERATE REPORT + SAVE RESULT
    # ========================================================

    def finalize_investigation(

        self,

        environment,

        decision
    ):

        # ----------------------------------------------------
        # GENERATE MARKDOWN / JSON REPORT
        # ----------------------------------------------------

        try:

            report_result = generate_report(

                environment,

                self.history,

                decision
            )


            print()

            print(
                "========================================"
            )

            print(
                "       INVESTIGATION REPORT"
            )

            print(
                "========================================"
            )


            if report_result is not None:

                print(

                    f"Report generated: "
                    f"{report_result}"
                )

            else:

                print(
                    "Investigation report generated."
                )


            print(
                "========================================"
            )


        except Exception as error:

            print()

            print(
                "WARNING: Could not generate "
                "investigation report."
            )

            print(
                f"Report error: {error}"
            )


        # ----------------------------------------------------
        # SAVE PERSISTENT RESULT
        # ----------------------------------------------------

        try:

            save_investigation_result(

                environment=environment,

                diagnosis=decision.get(
                    "hypothesis"
                ),

                confidence=float(

                    decision.get(

                        "confidence",

                        0.0
                    )
                ),

                probes_used=len(
                    self.observations
                )
            )


        except Exception as error:

            print()

            print(

                "WARNING: Could not save "
                "investigation result."
            )

            print(
                f"Result logger error: {error}"
            )


    # ========================================================
    # AUTONOMOUS INVESTIGATION LOOP
    # ========================================================

    def investigate(
        self,
        environment
    ):

        print()

        print(
            "========================================"
        )

        print(
            "     PATHPROBE-AI"
        )

        print(
            "     HYBRID AUTONOMOUS AGENT"
        )

        print(
            "========================================"
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # Environment is visible only to the test harness.
        # It is NEVER included in the Qwen prompt.
        # ----------------------------------------------------

        print(

            f"Testing simulation environment: "
            f"{environment}"
        )


        print(

            "The environment label is NOT provided "
            "to Qwen."
        )


        print(
            "========================================"
        )


        rate = 50

        used_rates = set()


        # ====================================================
        # PROBE LOOP
        # ====================================================

        for step in range(

            1,

            MAX_PROBES + 1
        ):


            # ------------------------------------------------
            # PREVENT DUPLICATE PROBES
            # ------------------------------------------------

            if rate in used_rates:

                unused = [

                    r

                    for r
                    in PROBE_RATES

                    if r not in used_rates
                ]


                if not unused:

                    break


                rate = unused[0]


            used_rates.add(rate)


            # ------------------------------------------------
            # REAL NS-3 MEASUREMENT
            # ------------------------------------------------

            observation = self.run_ns3(

                environment,

                rate
            )


            self.observations.append(

                observation
            )


            # ------------------------------------------------
            # QWEN REASONING
            # ------------------------------------------------

            decision = self.ask_llm()


            # ------------------------------------------------
            # DETERMINISTIC SAFETY POLICY
            # ------------------------------------------------

            decision = self.enforce_decision(

                decision
            )


            # ------------------------------------------------
            # SAVE HISTORY
            # ------------------------------------------------

            self.history.append({

                "observation":
                    observation,

                "decision":
                    decision
            })


            # ------------------------------------------------
            # DISPLAY
            # ------------------------------------------------

            self.print_state(

                step,

                observation,

                decision
            )


            # ------------------------------------------------
            # TERMINATE
            # ------------------------------------------------

            if decision.get(

                "stop",

                False

            ):

                print()

                print(
                    ">>> AGENT TERMINATED "
                    "INVESTIGATION"
                )


                print(

                    f">>> FINAL DIAGNOSIS: "
                    f"{decision.get('hypothesis')}"
                )


                print(

                    f">>> CONFIDENCE: "
                    f"{decision.get('confidence')}"
                )


                self.finalize_investigation(

                    environment,

                    decision
                )


                return decision


            # ------------------------------------------------
            # SELECT NEXT PROBE
            # ------------------------------------------------

            next_rate = decision.get(

                "next_probe_rate_pps"
            )


            try:

                next_rate = int(
                    next_rate
                )


            except (

                TypeError,

                ValueError

            ):

                next_rate = None


            # ------------------------------------------------
            # BAD / DUPLICATE QWEN RATE
            # ------------------------------------------------

            if (

                next_rate not in PROBE_RATES

                or

                next_rate in used_rates

            ):

                higher_rates = sorted(

                    [

                        r

                        for r
                        in PROBE_RATES

                        if (

                            r > rate

                            and

                            r not in used_rates
                        )
                    ]
                )


                if higher_rates:

                    next_rate = higher_rates[0]


                else:

                    unused = [

                        r

                        for r
                        in PROBE_RATES

                        if r not in used_rates
                    ]


                    if unused:

                        next_rate = unused[0]

                    else:

                        break


            rate = next_rate


        # ====================================================
        # MAXIMUM PROBE BUDGET REACHED
        # ====================================================

        print()

        print(
            ">>> MAXIMUM PROBE BUDGET REACHED"
        )


        final_evidence = calculate_evidence(

            self.observations
        )


        print(

            f">>> EVIDENCE ENGINE RESULT: "
            f"{final_evidence['classification']}"
        )


        # ----------------------------------------------------
        # DETERMINISTIC FINAL CLASSIFICATION
        # ----------------------------------------------------

        if (

            final_evidence[
                "classification"
            ]

            !=

            "UNCERTAIN"

        ):

            final_decision = {

                "hypothesis":
                    final_evidence[
                        "classification"
                    ],

                "confidence":
                    0.90,

                "reasoning":
                    "Final deterministic evidence "
                    "classification after the maximum "
                    "probe budget was reached.",

                "evidence":
                    final_evidence[
                        "signals"
                    ],

                "next_probe_rate_pps":
                    None,

                "stop":
                    True
            }


            print(

                f">>> FINAL DIAGNOSIS: "
                f"{final_decision['hypothesis']}"
            )


            self.finalize_investigation(

                environment,

                final_decision
            )


            return final_decision


        # ----------------------------------------------------
        # FINAL QWEN DECISION
        # ----------------------------------------------------

        final = self.ask_llm()


        final = self.enforce_decision(

            final
        )


        print(

            f">>> FINAL DIAGNOSIS: "
            f"{final.get('hypothesis')}"
        )


        print(

            f">>> CONFIDENCE: "
            f"{final.get('confidence')}"
        )


        self.finalize_investigation(

            environment,

            final
        )


        return final


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "Choose hidden simulation environment:"
    )

    print()

    print(
        "1. E0 - NORMAL"
    )

    print(
        "2. E1 - RATE_LIMITED"
    )

    print(
        "3. E2 - DELAY"
    )

    print()


    choice = input(

        "Enter environment (1/2/3): "
    ).strip()


    environment_map = {

        "1":
            "E0",

        "2":
            "E1",

        "3":
            "E2"
    }


    if choice not in environment_map:

        raise SystemExit(

            "\nInvalid choice. "
            "Enter 1, 2, or 3.\n"
        )


    agent = AutonomousPathProbe()


    agent.investigate(

        environment_map[choice]
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
