"""Prepare the reviewer-facing side of a BJM paired evaluation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
import unicodedata
from urllib.parse import unquote


SEPARATOR_RUNS = re.compile(r"/+")
DOT_SEGMENTS = re.compile(r"(?<![^/])\./")
WHITESPACE = re.compile(r"\s+")
MARKER_EDGES = re.compile(r"^[\s/]+|[\s/]+$")


def encode_json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def drop_format_characters(value):
    table = {ord(character): None for character in set(value) if unicodedata.category(character) == "Cf"}
    return value.translate(table) if table else value


def tidy_separators(value):
    return DOT_SEGMENTS.sub("", SEPARATOR_RUNS.sub("/", value))


def normalize(value):
    """Fold case, full-width forms, invisible characters and path separators the same way."""
    value = unicodedata.normalize("NFKC", value).casefold()
    return tidy_separators(drop_format_characters(value).replace("\\", "/"))


def forms(value):
    normalized = normalize(value)
    return normalized, tidy_separators(WHITESPACE.sub("", normalized))


def marker_forms(value):
    found = set()
    for form in forms(value):
        form = MARKER_EDGES.sub("", form)
        if not form:
            raise ValueError("identity markers must contain text")
        found.add(form)
    return found


def text_forms(value):
    found = set(forms(value))
    if "%" in value:
        found.update(forms(unquote(value)))
    return found


def read_text(role, path):
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{role} is not valid UTF-8 (byte {error.start})") from None


def read_inputs(brief_path, baseline_path, candidate_path, identity_markers):
    paths = {"brief": brief_path, "baseline": baseline_path, "candidate": candidate_path}
    texts = {role: read_text(role, path) for role, path in paths.items()}
    markers = set()
    for value in (*identity_markers, *(str(path) for path in (baseline_path, candidate_path)),
                  *(path.name for path in (baseline_path, candidate_path))):
        markers.update(marker_forms(value))
    for role, value in texts.items():
        if not drop_format_characters(value).strip():
            raise ValueError(f"{role} is empty")
        if any(marker in form for form in text_forms(value) for marker in markers):
            raise ValueError(f"{role} contains a known version identifier; inspect the material privately")
    return texts


def build(texts):
    roles = ("baseline", "candidate")
    if secrets.randbelow(2):
        roles = roles[::-1]
    mapping = dict(zip(("A", "B"), roles))
    packet = encode_json({"brief": texts["brief"], "outputs": {
        label: texts[role] for label, role in mapping.items()
    }})
    key = encode_json({"packet_sha256": hashlib.sha256(packet).hexdigest(), "roles": mapping})
    return packet, key


def prepare(brief_path, baseline_path, candidate_path, identity_markers):
    return build(read_inputs(brief_path, baseline_path, candidate_path, identity_markers))


def layout(text):
    crlf = text.count("\r\n")
    styles = [name for name, count in (("CRLF", crlf), ("LF", text.count("\n") - crlf),
                                       ("CR", text.count("\r") - crlf)) if count]
    body = text.rstrip("\r\n")
    ending = text[len(body):]
    return {
        "byte order mark": text.startswith("\ufeff"),
        "line endings": "+".join(styles) or None,
        "line breaks at the end": ending.count("\n") + ending.count("\r") - ending.count("\r\n"),
    }


def format_differences(first, second):
    """Name layout differences reviewers can see; the packet keeps both texts unchanged."""
    first, second = layout(first), layout(second)
    return [name for name in first if first[name] != second[name]
            and not (name == "line endings" and None in (first[name], second[name]))]


def create_new(path, mode):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    return os.fdopen(os.open(path, flags, mode), "wb")


def silence(stream):
    """Send output still buffered after a failed write to the null device, so exit reports one error."""
    try:
        descriptor = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(descriptor, stream.fileno())
        finally:
            os.close(descriptor)
    except (AttributeError, OSError, ValueError):
        pass


def tell(message):
    """Write to standard error; a closed or full standard error must not change the outcome."""
    stderr = sys.stderr
    if stderr is None:
        return
    try:
        stderr.write(message)
        stderr.flush()
    except (OSError, ValueError):
        silence(stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="baseline task output as UTF-8 text")
    parser.add_argument("candidate", type=Path, help="candidate task output as UTF-8 text")
    parser.add_argument("--brief", type=Path, required=True, help="shared task and review criteria")
    parser.add_argument("--key-out", type=Path, required=True,
                        help="new mapping file; keep it away from reviewers")
    parser.add_argument("--packet-out", type=Path,
                        help="new reviewer packet file (default: standard output)")
    parser.add_argument("--identity-marker", action="append", default=[], help="known version label or path to reject")
    args = parser.parse_args()
    created = []
    used_stdout = False
    try:
        texts = read_inputs(args.brief, args.baseline, args.candidate, args.identity_marker)
        packet, key = build(texts)
        stdout = None
        if args.packet_out is None:
            stdout = getattr(sys.stdout, "buffer", None)
            if stdout is None:
                raise OSError("standard output is not available; use --packet-out")
        with create_new(args.key_out, 0o600) as key_handle:
            created.append(args.key_out)
            if args.packet_out is not None:
                with create_new(args.packet_out, 0o666) as packet_handle:
                    created.append(args.packet_out)
                    packet_handle.write(packet)
            else:
                used_stdout = True
                stdout.write(packet)
                stdout.flush()
            key_handle.write(key)
    except (OSError, ValueError) as error:
        for path in reversed(created):
            try:
                os.unlink(path)
            except OSError:
                pass
        if used_stdout:
            silence(sys.stdout)
        tell(f"blind review: {error}\n")
        sys.exit(1)
    differences = format_differences(texts["baseline"], texts["candidate"])
    if differences:
        tell(f"blind review: note: the two outputs differ in {', '.join(differences)}; "
             "reviewers can see this, and the packet keeps both texts unchanged\n")


if __name__ == "__main__":
    main()
