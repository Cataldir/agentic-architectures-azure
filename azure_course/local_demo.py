"""Print predicted deterministic teaching decisions, without Azure or model SDK."""
from .policy import Evidence, release_decision
from .saga import Saga, record_step, begin_compensation, acknowledge_compensation


def main() -> None:
    mock = Evidence("prompt-v2", "synthetic-fixture", False, False, True,
                    1.0, 1.0, 0, 40)
    print("Fixture evidence release decision:", release_decision(mock))
    s = record_step(Saga("demo-1", "tenant-a"), "reserve", 0)
    s = record_step(s, "charge", 1)
    s = begin_compensation(s, outcome_known=True)
    print("Compensation order:", s.remaining)
    s = acknowledge_compensation(s, "charge", succeeded=False)
    print("Failed compensation state:", s.state)


if __name__ == "__main__":
    main()
