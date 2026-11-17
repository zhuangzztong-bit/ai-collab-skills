#!/usr/bin/env python3
"""Run an SQLite-backed BJM graph with a deterministic local demo adapter."""

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

from engine import Engine


def demo_handler(fail_before):
    def handle(node, dependencies):
        node_id = node["id"]
        if node_id == fail_before:
            raise TimeoutError("simulated timeout before any external action")
        inputs = node["inputs"]
        delay = inputs.get("delay_seconds", 0)
        if type(delay) not in (int, float) or not 0 <= delay <= 30:
            raise ValueError("delay_seconds must be between 0 and 30")
        if delay:
            time.sleep(delay)
        operation = inputs.get("operation", "draft")
        if operation == "review":
            if len(dependencies) != 1:
                raise ValueError("a demo review needs exactly one draft")
            draft_id, draft = next(iter(dependencies.items()))
            text = draft.get("text")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("demo review requires nonempty draft text")
            return {
                "verdict": "PASS",
                "reviewed_node": draft_id,
                "artifact_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "method": "simulated-review",
            }
        if operation != "draft":
            raise ValueError(f"unknown demo operation: {operation}")
        text = inputs.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("demo draft requires nonempty text")
        return {"text": text, "method": "simulated-builder"}

    return handle


def object_argument(value):
    try:
        data = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    if not isinstance(data, dict):
        raise argparse.ArgumentTypeError("provide a JSON object")
    return data


def parser_for_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init").add_argument("graph", type=Path)
    run = commands.add_parser("run")
    run.add_argument("--workers", type=int, default=2)
    run.add_argument("--fail-before", metavar="NODE", help="simulate a timeout in the demo adapter")
    commands.add_parser("status")
    commands.add_parser("events")
    commands.add_parser("retry").add_argument("node")
    edit = commands.add_parser("edit")
    edit.add_argument("node")
    edit.add_argument("inputs", type=object_argument)
    approve = commands.add_parser("approve")
    approve.add_argument("node")
    approve.add_argument("token")
    resolve = commands.add_parser("resolve")
    resolve.add_argument("node")
    resolve.add_argument("output", type=object_argument)
    return parser


def main():
    parser = parser_for_cli()
    args = parser.parse_args()
    try:
        if args.command != "init" and not args.db.is_file():
            raise ValueError("database does not exist; initialize the run first")
        engine = Engine(args.db)
        run_id = args.run_id
        if args.command == "init":
            graph = json.loads(args.graph.read_text(encoding="utf-8"))
            engine.init(run_id, graph)
        elif args.command == "run":
            if args.fail_before and args.fail_before not in engine.status(run_id)["nodes"]:
                raise ValueError(f"unknown demo fault node: {args.fail_before}")
            engine.run(run_id, demo_handler(args.fail_before), args.workers)
        elif args.command == "retry":
            engine.retry(run_id, args.node)
        elif args.command == "edit":
            engine.edit(run_id, args.node, args.inputs)
        elif args.command == "approve":
            engine.approve(run_id, args.node, args.token)
        elif args.command == "resolve":
            engine.resolve(run_id, args.node, args.output)
        result = engine.events(run_id) if args.command == "events" else engine.status(run_id)
    except (KeyError, OSError, RuntimeError, ValueError, sqlite3.Error) as error:
        parser.exit(2, f"workflow: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
