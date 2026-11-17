"""Exercise the two-chapter workflow across independent CLI processes."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent


def main():
    with TemporaryDirectory(prefix="bjm-graph-demo-") as folder:
        command = [
            sys.executable, "-B", str(ROOT / "workflow.py"),
            "--db", str(Path(folder) / "demo.sqlite"), "--run-id", "demo",
        ]

        def call(*args):
            result = subprocess.run(
                command + list(args), text=True, capture_output=True,
                encoding="utf-8", check=True,
            )
            return json.loads(result.stdout)

        call("init", str(ROOT / "examples/two_chapters.json"))
        failed = call("run", "--fail-before", "review-b")["nodes"]
        if failed["review-a"]["status"] != "SUCCEEDED" or failed["review-b"]["status"] != "FAILED":
            raise RuntimeError("the simulated failure did not isolate review-b")
        print("首次运行：第一章审查已保存，第二章模拟超时。")

        call("retry", "review-b")
        resumed = call("run")["nodes"]
        old_token = resumed["approve"]["token"]
        if not old_token or resumed["review-a"]["attempt"] != failed["review-a"]["attempt"]:
            raise RuntimeError("resume did not reuse the first chapter review")
        print("重新打开数据库：只补跑第二章审查，两章汇合后等待批准。")

        call("edit", "draft-b", '{"text":"第二章修订：接班人提前到值班台。"}')
        revised = call("run")["nodes"]
        new_token = revised["approve"]["token"]
        if not new_token or new_token == old_token:
            raise RuntimeError("new evidence did not invalidate the old approval")
        stale = subprocess.run(
            command + ["approve", "approve", "--", old_token],
            capture_output=True, encoding="utf-8",
        )
        if stale.returncode != 2 or "stale or invalid approval token" not in stale.stderr:
            raise RuntimeError("the old approval token was not rejected")
        done = call("approve", "approve", "--", new_token)["nodes"]
        if done["approve"]["status"] != "SUCCEEDED":
            raise RuntimeError("the current approval did not complete")
        if done["review-a"]["attempt"] != failed["review-a"]["attempt"]:
            raise RuntimeError("a change to the second chapter reran the first")
        print("第二章改稿：旧令牌被拒绝，新版批准成功，第一章审查未重跑。")
        print(f"已记录 {len(call('events'))} 条执行事件。")


if __name__ == "__main__":
    main()
