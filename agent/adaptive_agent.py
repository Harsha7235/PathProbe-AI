import math


class PathProbeAgent:

    def __init__(self):

        self.observations = []

        self.hypotheses = {
            "NORMAL": 0.50,
            "RATE_LIMITED": 0.50
        }

        self.available_probes = [
            {
                "name": "P1_BASELINE",
                "rate": 50
            },
            {
                "name": "P3_LOW_RATE",
                "rate": 100
            },
            {
                "name": "P3_HIGH_RATE",
                "rate": 200
            },
            {
                "name": "P3_STRESS",
                "rate": 500
            }
        ]

    # --------------------------------------------------------
    # RECORD OBSERVATION
    # --------------------------------------------------------

    def observe(
        self,
        rate,
        packet_loss,
        delay,
        throughput
    ):

        observation = {
            "rate": rate,
            "packet_loss": packet_loss,
            "delay": delay,
            "throughput": throughput
        }

        self.observations.append(
            observation
        )

        self.update_hypotheses(
            observation
        )

    # --------------------------------------------------------
    # UPDATE HYPOTHESES
    # --------------------------------------------------------

    def update_hypotheses(
        self,
        observation
    ):

        loss = observation["packet_loss"]
        delay = observation["delay"]

        # Strong evidence of abnormal behavior
        if loss >= 20 and delay >= 100:

            self.hypotheses[
                "RATE_LIMITED"
            ] += 0.45

            self.hypotheses[
                "NORMAL"
            ] -= 0.25

        # Moderate evidence
        elif loss > 0 or delay > 50:

            self.hypotheses[
                "RATE_LIMITED"
            ] += 0.20

            self.hypotheses[
                "NORMAL"
            ] -= 0.10

        # Normal observation
        else:

            self.hypotheses[
                "NORMAL"
            ] += 0.10

        self.normalize()

    # --------------------------------------------------------
    # NORMALIZE CONFIDENCE
    # --------------------------------------------------------

    def normalize(self):

        for key in self.hypotheses:

            if self.hypotheses[key] < 0:
                self.hypotheses[key] = 0

        total = sum(
            self.hypotheses.values()
        )

        if total == 0:

            for key in self.hypotheses:
                self.hypotheses[key] = 0.5

            return

        for key in self.hypotheses:

            self.hypotheses[key] /= total

    # --------------------------------------------------------
    # SELECT NEXT PROBE
    # --------------------------------------------------------

    def choose_probe(self):

        if not self.observations:

            return self.available_probes[0]

        confidence = max(
            self.hypotheses.values()
        )

        # If already highly confident,
        # stop probing.
        if confidence >= 0.90:

            return None

        tested_rates = {
            observation["rate"]
            for observation in self.observations
        }

        # Prefer the boundary probe.
        preferred_order = [
            100,
            200,
            500,
            50
        ]

        for rate in preferred_order:

            if rate not in tested_rates:

                for probe in self.available_probes:

                    if probe["rate"] == rate:

                        return probe

        return None

    # --------------------------------------------------------
    # CURRENT DIAGNOSIS
    # --------------------------------------------------------

    def diagnosis(self):

        hypothesis = max(
            self.hypotheses,
            key=self.hypotheses.get
        )

        confidence = self.hypotheses[
            hypothesis
        ]

        return hypothesis, confidence

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def status(self):

        diagnosis, confidence = (
            self.diagnosis()
        )

        print()
        print("----------------------------------------")
        print("PATHPROBE-AI AGENT STATUS")
        print("----------------------------------------")

        print(
            f"NORMAL        : "
            f"{self.hypotheses['NORMAL']:.3f}"
        )

        print(
            f"RATE_LIMITED  : "
            f"{self.hypotheses['RATE_LIMITED']:.3f}"
        )

        print(
            f"Diagnosis     : {diagnosis}"
        )

        print(
            f"Confidence    : {confidence:.3f}"
        )

        print(
            f"Observations  : "
            f"{len(self.observations)}"
        )

        print("----------------------------------------")


# ============================================================
# DEMONSTRATION
# ============================================================

def main():

    agent = PathProbeAgent()

    print()
    print("========================================")
    print("       PATHPROBE-AI AGENT")
    print("       ADAPTIVE PROBE SELECTION")
    print("========================================")

    # Initial decision
    probe = agent.choose_probe()

    print()
    print(
        f"Initial probe: {probe}"
    )

    # Simulated observation from E1
    agent.observe(
        rate=100,
        packet_loss=0.0,
        delay=21.0,
        throughput=0.842
    )

    agent.status()

    # Agent chooses next probe
    probe = agent.choose_probe()

    print()
    print(
        f"Next probe: {probe}"
    )

    # Simulated E1 stress observation
    agent.observe(
        rate=200,
        packet_loss=21.2,
        delay=482.0,
        throughput=1.137
    )

    agent.status()

    # Final decision
    probe = agent.choose_probe()

    print()

    if probe is None:

        print(
            "Agent decision: STOP PROBING"
        )

    else:

        print(
            f"Agent decision: "
            f"run {probe['name']}"
        )

    diagnosis, confidence = (
        agent.diagnosis()
    )

    print()
    print("========================================")
    print("FINAL HYPOTHESIS")
    print("========================================")

    print(
        f"Behavior   : {diagnosis}"
    )

    print(
        f"Confidence : {confidence:.3f}"
    )

    print()


if __name__ == "__main__":
    main()
