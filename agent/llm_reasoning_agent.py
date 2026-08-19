import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://172.20.192.1:11434/api/generate"

# Change this to the model you actually have in Ollama.
MODEL = "qwen3:8b"


class GroundedPathProbeAgent:

    def __init__(self):

        self.observations = []

        self.hypotheses = [
            "NORMAL",
            "RATE_LIMITED",
            "DELAY"
        ]

    def build_prompt(self):

        evidence = json.dumps(
            self.observations,
            indent=2
        )

        return f"""
You are the reasoning component of PathProbe-AI,
an AI system for diagnosing hidden network-path behavior.

You MUST reason ONLY from the measured ns-3 observations
provided below.

Possible hypotheses:

1. NORMAL
2. RATE_LIMITED
3. DELAY

Observed evidence:

{evidence}

Interpret the measurements.

Important signatures:

- NORMAL:
  low delay and little/no packet loss.

- RATE_LIMITED:
  packet loss increases under offered load and delay
  becomes very high.

- DELAY:
  delay is persistently high while packet loss remains
  low.

Return ONLY valid JSON in exactly this structure:

{{
  "hypothesis": "NORMAL | RATE_LIMITED | DELAY",
  "confidence": 0.0,
  "evidence": [
    "short evidence statement"
  ],
  "alternative": "NORMAL | RATE_LIMITED | DELAY",
  "next_probe_rate_pps": 50,
  "stop": true
}}

Rules:

- confidence must be between 0 and 1.
- Do not invent measurements.
- Do not claim evidence that is not present.
- If evidence is insufficient, choose another probe.
- If evidence is strong enough, set stop to true.
"""

    def ask_llm(self):

        prompt = self.build_prompt()

        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        data = json.dumps(
            payload
        ).encode("utf-8")

        request = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=120
            ) as response:

                result = json.loads(
                    response.read()
                )

        except urllib.error.URLError as error:

            raise RuntimeError(
                "Could not connect to Ollama.\n"
                "Make sure Ollama is running and "
                "the model is installed.\n\n"
                f"Original error: {error}"
            )

        text = result.get(
            "response",
            ""
        )

        if not text:

            raise RuntimeError(
                "Ollama returned an empty response."
            )

        try:

            return json.loads(text)

        except json.JSONDecodeError:

            print("\nRaw LLM response:")
            print(text)

            raise RuntimeError(
                "LLM did not return valid JSON."
            )

    def add_observation(
        self,
        rate,
        packet_loss,
        delay,
        throughput
    ):

        observation = {
            "probe_rate_pps": rate,
            "packet_loss_percent": packet_loss,
            "average_delay_ms": delay,
            "throughput_mbps": throughput
        }

        self.observations.append(
            observation
        )

    def print_reasoning(self, decision):

        print()
        print("========================================")
        print("       PATHPROBE-AI LLM REASONING")
        print("========================================")

        print(
            f"Hypothesis : "
            f"{decision.get('hypothesis')}"
        )

        print(
            f"Confidence : "
            f"{decision.get('confidence')}"
        )

        print()
        print("Evidence:")

        for evidence in decision.get(
            "evidence",
            []
        ):

            print(
                f"  - {evidence}"
            )

        print()
        print(
            f"Alternative: "
            f"{decision.get('alternative')}"
        )

        print(
            f"Next probe : "
            f"{decision.get('next_probe_rate_pps')} pps"
        )

        print(
            f"Stop       : "
            f"{decision.get('stop')}"
        )

        print(
            "========================================"
        )


def main():

    agent = GroundedPathProbeAgent()

    print()
    print("========================================")
    print("       PATHPROBE-AI")
    print("       GROUNDED LLM AGENT")
    print("========================================")

    # --------------------------------------------------------
    # IMPORTANT:
    # These are REAL measurements from your ns-3 experiments.
    # The LLM does not generate them.
    # --------------------------------------------------------

    agent.add_observation(
        rate=50,
        packet_loss=0.0,
        delay=21.0,
        throughput=0.4214
    )

    decision = agent.ask_llm()

    agent.print_reasoning(
        decision
    )


if __name__ == "__main__":
    main()
