import argparse
import json
import sys

from dotenv import load_dotenv

from workflow import classifier_node, preprocess_node, router_edge


def read_ticket_text(args: argparse.Namespace) -> str:
    if args.ticket_text:
        return " ".join(args.ticket_text).strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    return ""


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Classify and route a bank support ticket."
    )
    parser.add_argument(
        "ticket_text",
        nargs="*",
        help="Customer ticket text. If omitted, text is read from stdin.",
    )

    args = parser.parse_args()
    raw_input = read_ticket_text(args)

    if not raw_input:
        parser.error("Provide ticket text as an argument or through stdin.")

    state = {"raw_input": raw_input}
    state.update(preprocess_node(state))
    state.update(classifier_node(state))

    route = router_edge(state)

    print("\nClassification result:")
    print(json.dumps(state["analysis"], indent=2))
    print(f"\nRouting decision: {route}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
