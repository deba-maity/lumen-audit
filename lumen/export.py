"""Portable evidence reports; no scripts or external assets."""
import csv
from datetime import datetime, timezone
from html import escape
import io

from .assistant import size
from .rules import describe_file, timestamp_label


def spreadsheet_text(value):
    """Prevent inventoried strings from becoming spreadsheet formulas."""
    value = str(value)
    if value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def csv_inventory(report):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(["Name", "Path", "Category", "Logical bytes", "Modified (UTC)",
                     "Raw access timestamp (UTC)", "Last human-opened", "Likely purpose",
                     "Removal could affect", "Finding IDs"])
    findings = {}
    for finding in report["findings"]:
        for path in finding["paths"]:
            findings.setdefault(path, []).append(finding["id"])
    for file in report["files"]:
        description = describe_file(file)
        writer.writerow([spreadsheet_text(file["name"]), spreadsheet_text(file["path"]),
                         spreadsheet_text(file["category"]), file["size"],
                         timestamp_label(file["modified"]), timestamp_label(file["accessed"]), "Unknown",
                         spreadsheet_text(file.get("purpose") or description["purpose"]),
                         spreadsheet_text(file.get("consequence") or description["consequence"]),
                         spreadsheet_text("; ".join(findings.get(file["path"], [])))])
    # UTF-8 BOM makes non-ASCII names readable in common spreadsheet applications.
    return "\ufeff" + output.getvalue()


def html_report(report):
    esc = lambda value: escape(str(value), quote=True)
    findings = "".join(f"<article><div class='tag'>{esc(item['kind'])} · {esc(item['confidence'])}</div><h2>{esc(item['title'])} <span>{esc(size(item['bytes']))}</span></h2><p class='path'>{esc(item['path'])}</p><p>{esc(item['purpose'])}</p><ul>{''.join('<li>' + esc(line) + '</li>' for line in item['evidence'])}</ul><p><b>Review:</b> {esc(item['recommendation'])}</p><p><b>Removal could affect:</b> {esc(item['consequence'])}</p><details open><summary>All locations ({len(item['paths'])})</summary><ul>{''.join('<li class=path>' + esc(path) + '</li>' for path in item['paths'])}</ul></details></article>" for item in report["findings"])
    skipped = "".join(f"<li><code>{esc(item['path'])}</code> — {esc(item['reason'])}</li>" for item in report["skipped"])
    apps = "".join(f"<tr><td>{esc(app['name'])}</td><td>{esc(app['publisher'])}</td><td>{esc(app['version'])}</td><td>Unknown</td></tr>" for app in report["apps"])
    summary = report["summary"]
    timestamp = datetime.fromtimestamp(report["created"], timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    warnings = "".join(f"<li>{esc(warning)}</li>" for warning in report["warnings"])
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lumen · Storage report</title><style>
    *{{box-sizing:border-box}}body{{background:#f7f7f2;color:#263f38;font:16px/1.6 system-ui,sans-serif;max-width:960px;margin:0 auto;padding:50px 24px}}h1{{font-size:48px;letter-spacing:-2px;margin:10px 0}}h2{{font-size:21px}}h2 span{{float:right;font-weight:400}}.tag{{text-transform:uppercase;letter-spacing:1.5px;font-size:11px}}.stats{{display:flex;gap:30px;flex-wrap:wrap;margin:30px 0}}.stats strong{{font-size:28px;display:block}}article{{background:white;border:1px solid #dce2d9;border-radius:14px;padding:24px;margin:16px 0;break-inside:avoid}}.path,code{{overflow-wrap:anywhere;font-size:13px}}table{{width:100%;text-align:left;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #ddd}}footer{{margin-top:40px;font-size:13px}}@media print{{body{{background:white;padding:0}}details{{display:block}}}}
    </style><header><div class="tag">Lumen / {'Fictional demo report' if report['demo'] else 'Local storage report'}</div><h1>A little clarity.<br>A lighter laptop.</h1><p><b>{esc(report['name'])}</b><br>{esc(timestamp)} · Snapshot {esc(report['id'])}</p><p>Selected folders: {esc(', '.join(report['roots']))}</p></header><div class="stats"><div><strong>{esc(size(summary['bytes']))}</strong>inventoried logical size</div><div><strong>{summary['files']:,}</strong>files inventoried</div><div><strong>{esc(size(summary['review_bytes']))}</strong>under review</div></div><p><b>Read-only recommendations.</b> No audited files or settings were modified. “Under review” is not guaranteed reclaimable space. Last human-opened time is unknown. Coverage excludes protected, linked, inaccessible, and cloud-only locations. Reads may update OS-managed access metadata.</p><ul>{warnings}</ul><h2>Review queue</h2>{findings or '<p>No review candidates were found within this scope.</p>'}<h2>Applications</h2><p>Declared registry metadata only; not a complete application inventory. Install/service dates are not first-install dates.</p><table><thead><tr><th>Name</th><th>Publisher</th><th>Version</th><th>Last used</th></tr></thead><tbody>{apps}</tbody></table><h2>Coverage</h2><p>{report['coverage']['skipped']:,} items skipped. {'Inventory limit reached.' if report['coverage']['limited'] else 'Inventory completed within configured bounds.'} Duplicate hashing: {'enabled' if report['coverage']['hashing'] else 'disabled'}.</p><ul>{skipped}</ul><footer>Generated by Lumen. Report includes local paths and filenames; review it before sharing. AI explanations are not included in this evidence report.</footer></html>"""
