import sys

from friday.core import Orchestrator


def main() -> int:
    query = " ".join(sys.argv[1:]).strip() or "hello"
    response = Orchestrator().run(query)
    print(response.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
