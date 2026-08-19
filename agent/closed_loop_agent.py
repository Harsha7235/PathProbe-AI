import re
import subprocess
from pathlib import Path


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

E2_EXECUTABLE = (
    NS3_DIR
    / "build"
    / "scratch"
    / "ns3.48-pathprobe_delay_jitter-default"
)


class PathProbeAgent:

    def __init__(self):

        self.observations = []

        self.hypotheses = {
            "NORMAL": 0.34,
            "RATE_LIMITED": 0.33,
            "DELAY": 0.33
        }

        # Probes ordered from cheap/low stress
        # to increasingly discriminative probes.
        self.probe_sequence = [
            50,
            100,
            200,
            500
        ]

    # ========================================================
    # RUN NS-3
    # ========================================================

    def run_ns3(self, environment, rate):

        executables = {
            "E0": E0_EXECUTABLE,
            "E1": E1_EXECUTABLE,
            "E2": E2_EXECUTABLE
        }

        if environment not in executables:
            raise ValueError(
                f"Unknown environment: {environment}"
            )

        executable = executables[environment]

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

    # ========================================================
    # PARSE NS-3
    # ========================================================

    def parse_output(self, output):

        def extract(pattern):

            match = re.search(
                pattern,
                output
            )

            if not match:

                raise ValueError(
                    f"Could not extract: {pattern}"
                )

            return float(
                match.group(1)
            )

        return {
            "packet_loss": extract(
                r"Packet Loss\s*:\s*([\d.]+)"
            ),

            "throughput": extract(
                r"Throughput\s*:\s*([\d.]+)"
            ),

            "delay": extract(
                r"Average Delay\s*:\s*([\d.]+)"
            )
        }

    # ========================================================
    # UPDATE HYPOTHESES
    # ========================================================

    def update_beliefs(self, observation):

        loss = observation["packet_loss"]
        delay = observation["delay"]

        # ----------------------------------------------------
        # RATE-LIMITED SIGNATURE
        # ----------------------------------------------------

        if loss >= 20 and delay >= 100:

            self.hypotheses[
                "RATE_LIMITED"
            ] += 0.45

            self.hypotheses[
                "NORMAL"
            ] -= 0.20

            self.hypotheses[
                "DELAY"
            ] -= 0.20

        # ----------------------------------------------------
        # DELAY SIGNATURE
        # ----------------------------------------------------

        elif delay >= 70 and loss < 5:

            self.hypotheses[
                "DELAY"
            ] += 0.45

            self.hypotheses[
                "NORMAL"
            ] -= 0.20

            self.hypotheses[
                "RATE_LIMITED"
            ] -= 0.20

        # ----------------------------------------------------
        # MODERATE ABNORMALITY
        # ----------------------------------------------------

        elif loss > 0 or delay > 50:

            self.hypotheses[
                "RATE_LIMITED"
            ] += 0.10

            self.hypotheses[
                "DELAY"
            ] += 0.15

            self.hypotheses[
                "NORMAL"
            ] -= 0.15

        # ----------------------------------------------------
        # NORMAL
        # ----------------------------------------------------

        else:

            self.hypotheses[
                "NORMAL"
            ] += 0.15

            self.hypotheses[
                "RATE_LIMITED"
            ] -= 0.07

            self.hypotheses[
                "DELAY"
            ] -= 0.07

        self.normalize()

    # ========================================================
    # NORMALIZE
    # ========================================================

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

            for key in self.hypotheses:
                self.hypotheses[key] = 1 / 3

            return

        for key in self.hypotheses:

            self.hypotheses[key] /= total

    # ========================================================
    # SELECT NEXT PROBE
    # ========================================================

    def choose_next_probe(self):

        confidence = max(
            self.hypotheses.values()
        )

        # Stop if sufficiently confident.
        if confidence >= 0.90:

            return None

        tested = {
            observation["rate"]
            for observation in self.observations
        }

        for rate in self.probe_sequence:

            if rate not in tested:

                return rate

        return None

    # ========================================================
    # STATUS
    # ========================================================

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

        for hypothesis, probability in (
            self.hypotheses.items()
        ):

            print(
                f"{hypothesis:14}: "
                f"{probability:.3f}"
            )

        print(
            f"Diagnosis      : {diagnosis}"
        )

        print(
            f"Confidence     : {confidence:.3f}"
        )

        print(
            f"Probes used    : "
            f"{len(self.observations)}"
        )

        print("========================================")

    # ========================================================
    # CLOSED LOOP
    # ========================================================

    def investigate(self, environment):

        print()
        print("========================================")
        print("       PATHPROBE-AI CLOSED LOOP")
        print("       3-CLASS ENVIRONMENT TEST")
        print("========================================")

        print()
        print(
            "Hidden environment:"
            f" {environment}"
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
            f"Diagnosis   : {diagnosis}"
        )

        print(
            f"Confidence  : {confidence:.3f}"
        )

        print(
            f"Total probes: "
            f"{len(self.observations)}"
        )

        print("========================================")


def main():

    # ========================================================
    # GROUND TRUTH
    #
    # Change this ONLY for evaluation:
    #
    # E0 = NORMAL
    # E1 = RATE_LIMITED
    # E2 = DELAY
    #
    # The agent does NOT receive this value as evidence.
    # ========================================================

    hidden_environment = "E0"

    agent = PathProbeAgent()

    agent.investigate(
        hidden_environment
    )


if __name__ == "__main__":
    main()
