import re
import subprocess
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

NS3_DIR = Path("/home/harsha/ns-3.48")

E0_EXECUTABLE = (
    NS3_DIR
    / "build"
    / "scratch"
    / "ns3.48-pathprobe_rate-default"
)

E1_EXECUTABLE = (
    NS3_DIR
    / "build"
    / "scratch"
    / "ns3.48-pathprobe_rate_limited-default"
)


# ============================================================
# ADAPTIVE AGENT
# ============================================================

class PathProbeAgent:

    def __init__(self):

        self.observations = []

        self.hypotheses = {
            "NORMAL": 0.50,
            "RATE_LIMITED": 0.50
        }

        self.probe_sequence = [
            50,
            100,
            200,
            500
        ]

    # --------------------------------------------------------
    # RUN NS-3
    # --------------------------------------------------------

    def run_ns3(self, environment, rate):

        if environment == "E0":
            executable = E0_EXECUTABLE

        elif environment == "E1":
            executable = E1_EXECUTABLE

        else:
            raise ValueError(
                f"Unknown environment: {environment}"
            )

        command = [
            str(executable),
            f"--packetsPerSecond={rate}"
        ]

        if environment == "E1":
            command.append(
                "--rateLimit=1Mbps"
            )

        print()
        print("----------------------------------------")
        print("RUNNING PROBE")
        print("----------------------------------------")
        print(
            f"Environment : {environment}"
        )
        print(
            f"Probe rate  : {rate} packets/sec"
        )

        result = subprocess.run(
            command,
            cwd=NS3_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:

            print(result.stderr)

            raise RuntimeError(
                "ns-3 experiment failed"
            )

        print(result.stdout)

        return result.stdout

    # --------------------------------------------------------
    # PARSE NS-3 OUTPUT
    # --------------------------------------------------------

    def parse_output(self, output):

        def extract(pattern):

            match = re.search(
                pattern,
                output
            )

            if not match:

                raise ValueError(
                    f"Could not find: {pattern}"
                )

            return float(
                match.group(1)
            )

        return {
            "packet_loss":
                extract(
                    r"Packet Loss\s*:\s*([\d.]+)"
                ),

            "throughput":
                extract(
                    r"Throughput\s*:\s*([\d.]+)"
                ),

            "delay":
                extract(
                    r"Average Delay\s*:\s*([\d.]+)"
                )
        }

    # --------------------------------------------------------
    # UPDATE BELIEFS
    # --------------------------------------------------------

    def update_beliefs(self, observation):

        loss = observation["packet_loss"]
        delay = observation["delay"]

        if loss >= 20 and delay >= 100:

            self.hypotheses[
                "RATE_LIMITED"
            ] += 0.45

            self.hypotheses[
                "NORMAL"
            ] -= 0.25

        elif loss > 0 or delay > 50:

            self.hypotheses[
                "RATE_LIMITED"
            ] += 0.20

            self.hypotheses[
                "NORMAL"
            ] -= 0.10

        else:

            self.hypotheses[
                "NORMAL"
            ] += 0.10

        self.normalize()

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    def normalize(self):

        for key in self.hypotheses:

            self.hypotheses[key] = max(
                0.0,
                self.hypotheses[key]
            )

        total = sum(
            self.hypotheses.values()
        )

        if total == 0:

            self.hypotheses = {
                "NORMAL": 0.5,
                "RATE_LIMITED": 0.5
            }

            return

        for key in self.hypotheses:

            self.hypotheses[key] /= total

    # --------------------------------------------------------
    # SELECT NEXT PROBE
    # --------------------------------------------------------

    def choose_next_probe(self):

        confidence = max(
            self.hypotheses.values()
        )

        # Stop when sufficiently confident.
        if confidence >= 0.90:

            return None

        tested = {
            obs["rate"]
            for obs in self.observations
        }

        for rate in self.probe_sequence:

            if rate not in tested:

                return rate

        return None

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def print_status(self):

        diagnosis = max(
            self.hypotheses,
            key=self.hypotheses.get
        )

        confidence = self.hypotheses[
            diagnosis
        ]

        print()
        print("========================================")
        print("       AGENT BELIEF STATE")
        print("========================================")

        print(
            f"NORMAL       : "
            f"{self.hypotheses['NORMAL']:.3f}"
        )

        print(
            f"RATE_LIMITED : "
            f"{self.hypotheses['RATE_LIMITED']:.3f}"
        )

        print(
            f"Diagnosis    : {diagnosis}"
        )

        print(
            f"Confidence   : {confidence:.3f}"
        )

        print(
            f"Probes used  : "
            f"{len(self.observations)}"
        )

        print("========================================")

    # --------------------------------------------------------
    # CLOSED LOOP
    # --------------------------------------------------------

    def investigate(self, environment):

        print()
        print("========================================")
        print("       PATHPROBE-AI CLOSED LOOP")
        print("========================================")
        print()
        print(
            "Environment is hidden from the agent."
        )

        while True:

            rate = self.choose_next_probe()

            if rate is None:
                break

            output = self.run_ns3(
                environment,
                rate
            )

            measurement = self.parse_output(
                output
            )

            measurement["rate"] = rate

            self.observations.append(
                measurement
            )

            self.update_beliefs(
                measurement
            )

            self.print_status()

        diagnosis = max(
            self.hypotheses,
            key=self.hypotheses.get
        )

        confidence = self.hypotheses[
            diagnosis
        ]

        print()
        print("========================================")
        print("       FINAL AGENT DECISION")
        print("========================================")

        print(
            f"Diagnosis  : {diagnosis}"
        )

        print(
            f"Confidence : {confidence:.3f}"
        )

        print(
            f"Total probes: "
            f"{len(self.observations)}"
        )

        print(
            "========================================"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Change ONLY this value when testing.
    #
    # E0 = normal
    # E1 = rate limited
    #
    # The agent itself does not use this value to diagnose.
    # It is only the hidden ground truth used by the experiment.
    # --------------------------------------------------------

    hidden_environment = "E1"

    agent = PathProbeAgent()

    agent.investigate(
        hidden_environment
    )


if __name__ == "__main__":
    main()
