import asyncio
import logging
import sys

from friday.core import Orchestrator


def main() -> int:
    args = sys.argv[1:]

    # Voice server mode
    if "--voice-server" in args:
        port = 8080
        if "--port" in args:
            idx = args.index("--port")
            if idx + 1 < len(args):
                port = int(args[idx + 1])
        elif "-p" in args:
            idx = args.index("-p")
            if idx + 1 < len(args):
                port = int(args[idx + 1])

        logging.basicConfig(level=logging.INFO)
        from friday.voice_server import voice_server_main
        asyncio.run(voice_server_main(port=port))
        return 0

    # Default: run one query
    query = " ".join(args).strip() or "hello"
    response = Orchestrator().run(query)
    print(response.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
