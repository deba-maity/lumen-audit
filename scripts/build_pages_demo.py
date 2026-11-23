"""Build a static Lumen demo from its fictional snapshots."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lumen import __version__
from lumen.assistant import evidence_answer
from lumen.demo import demo_reports
from lumen.export import csv_inventory, html_report
from lumen.store import compare
from package import build


def build_demo(output):
    output.mkdir(parents=True, exist_ok=False)
    exports = output / "exports"
    exports.mkdir()
    for asset in ("app.js", "pages-demo.js", "styles.css", "favicon.svg"):
        shutil.copyfile(ROOT / "web" / asset, output / asset)

    html = (ROOT / "web/index.html").read_text(encoding="utf-8")
    for asset in ("app.js", "styles.css", "favicon.svg"):
        html = html.replace(f'"/{asset}"', f'"./{asset}"')
    html = html.replace('<script src="./app.js" defer></script>',
                        '<script src="./pages-demo.js" defer></script>\n  <script src="./app.js" defer></script>')
    (output / "index.html").write_text(html, encoding="utf-8")
    (output / ".nojekyll").touch()
    shutil.copyfile(build(), output / "lumen-audit.zip")
    shutil.copyfile(ROOT / "LICENSE", output / "LICENSE")

    reports = demo_reports()
    history_keys = ("id", "name", "created", "roots", "summary", "demo")
    data = {
        "version": __version__,
        "history": [{key: report[key] for key in history_keys} for report in reports],
        "comparisons": {
            before["id"]: {
                after["id"]: compare(before, after) for after in reports if before["created"] < after["created"]
            } for before in reports
        },
        "reports": {}
    }
    topics = ("overview", "duplicates", "generated project folders", "privacy", "last opened")
    for report in reports:
        report_id = report["id"]
        data["reports"][report_id] = {
            "report": report,
            "topics": {topic: evidence_answer(report, topic) for topic in topics},
            "files": {file["id"]: evidence_answer(report, "", file_id=file["id"]) for file in report["files"]},
            "findings": {item["id"]: evidence_answer(report, "", finding_id=item["id"]) for item in report["findings"]}
        }
        (exports / f"{report_id}.json").write_text(json.dumps(report), encoding="utf-8")
        (exports / f"{report_id}.html").write_text(html_report(report), encoding="utf-8")
        (exports / f"{report_id}.csv").write_text(csv_inventory(report), encoding="utf-8")
    (output / "demo.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    build_demo(parser.parse_args().output)
