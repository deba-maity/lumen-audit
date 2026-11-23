"""Evidence-based interpretation. Nothing in this module modifies scanned files."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

DAY = 86400
MIB = 1024 ** 2
GIB = 1024 ** 3

CATEGORIES = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".epub"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".heic", ".raw", ".psd", ".avif", ".ico"},
    "Video & audio": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".flac", ".m4a", ".ogg"},
    "Archives & installers": {".zip", ".7z", ".rar", ".tar", ".gz", ".iso", ".msi", ".exe", ".dmg", ".pkg", ".deb", ".rpm"},
    "Development": {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".html", ".css", ".java", ".cpp", ".c", ".h", ".rs", ".go", ".ipynb", ".toml", ".yaml", ".yml", ".sql", ".lock"},
}
PROTECTED_NAMES = {"windows", "program files", "program files (x86)", "programdata", "$recycle.bin", "system volume information", "recovery", "boot", "efi", ".git", ".ssh", ".gnupg", ".aws", ".azure", ".kube", "proc", "sys", "dev", "etc", "bin", "sbin", "lib", "lib64", "usr", "system", "library"}
GENERATED = {
    "node_modules": ("JavaScript dependencies", "Installed packages used by a JavaScript project.", "Reinstallation requires the package manifest, access to the packages, and any credentials. Local patches or unpublished packages may not be recoverable."),
    "__pycache__": ("Python bytecode cache", "Compiled bytecode created when Python modules run.", "Normally recreated from the original Python source. Keep it if the source is unavailable; a running process may still use these files."),
    ".pytest_cache": ("Pytest cache", "Local test-run metadata, such as previously failed tests.", "Pytest usually recreates this metadata. Removing it loses local test history."),
    ".next": ("Next.js build output", "Generated output and cache for a Next.js application.", "A running app may depend on this output. Rebuilding requires source code and working dependencies."),
    ".venv": ("Python virtual environment", "An isolated Python interpreter and project dependencies.", "Recreating it needs dependency specifications and available packages. Editable installs or local changes may be lost."),
}


def uid(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "surrogatepass")).hexdigest()[:20]


def timestamp_label(value: float) -> str:
    if value is None:
        return "Unknown"
    try:
        return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OSError, OverflowError):
        return "Outside the supported date range (raw timestamp retained in the inventory)"


def category(path: Path) -> str:
    return next((key for key, extensions in CATEGORIES.items() if path.suffix.lower() in extensions), "Other")


def generated_info(path: Path, root: Path):
    # Include a selected generated root, not unrelated ancestors outside scope.
    parts = (root.name,) + path.relative_to(root).parts[:-1]
    for index, part in enumerate(parts):
        if part.lower() in GENERATED:
            directory = root if index == 0 else root.joinpath(*parts[1:index + 1])
            return str(directory), part.lower()
    return None


def describe_file(record: dict) -> dict:
    ext = Path(record["path"]).suffix.lower()
    category_name = record["category"]
    descriptions = {
        "Documents": "A document or structured text file. Its importance cannot be inferred from its age or name.",
        "Images": "An image or design asset. It may be an original, an export, or part of an application.",
        "Video & audio": "A media file. Large size is normal for recordings and high-quality exports.",
        "Archives & installers": "An archive, disk image, or executable package. It may be a backup, installer, or a portable application.",
        "Development": "Source code, configuration, or project data. It may be required to build or run a project.",
        "Other": "An unclassified file. Lumen has not inspected its contents and cannot establish its purpose.",
    }
    known_names = {
        "package.json": "A JavaScript project's package manifest: scripts, package metadata, and declared dependencies. Removing it can prevent normal installation and builds.",
        "package-lock.json": "An npm dependency lockfile. It records exact dependency versions for reproducible installations; it is not a disposable cache.",
        "requirements.txt": "A conventional Python dependency list used to recreate an environment. Preserve it if the project is still needed.",
        "pyproject.toml": "Python project, build, and tool configuration. It may be required for packaging, dependency installation, and development tools.",
        "dockerfile": "Instructions for building a container image. The project may depend on it for development or deployment.",
        "readme.md": "Conventional project documentation. It may contain setup instructions and context needed to maintain the project.",
    }
    name = Path(record["path"]).name.lower()
    if name in known_names:
        description = known_names[name]
    elif record.get("generated"):
        description = GENERATED[record["generated"][1]][1] + " This classification comes from the containing folder's name."
    elif ext in {".gguf", ".safetensors", ".onnx"}:
        description = "A machine-learning model or model-weight file, based on its extension. Local AI applications may need it for inference. Replacing it can require a large download; availability and licensing have not been checked."
    elif ext in {".sqlite", ".sqlite3", ".db"}:
        description = "Likely a database or application data file, based on its extension. It may contain unique user data or application state; contents have not been inspected."
    elif ext in {".dll", ".so", ".dylib", ".pyd", ".node"}:
        description = "A native library or module, based on its extension. An application may load this file to function; it is not an independent document."
    elif ext == ".log":
        description = "Likely an application log, based on its extension. It may be useful for troubleshooting or record keeping; retention needs are unknown."
    elif ext in {".msi", ".dmg", ".pkg", ".deb", ".rpm"}:
        description = "An installation package. It may be needed to reinstall software, especially when the original download is unavailable."
    else:
        description = descriptions[category_name]
    return {"purpose": description, "consequence": "Removal may permanently lose this file or affect software that depends on it. Review its owner and role first."}


def findings_for(files: list[dict], duplicate_groups: list[dict], now: float) -> list[dict]:
    findings = []
    claimed = set()
    for group in duplicate_groups:
        paths = [item["path"] for item in group["files"]]
        claimed.update(paths)
        findings.append({
            "id": "dup-" + group["id"], "kind": "duplicates", "title": f"{len(paths)} matching copies of {Path(paths[0]).name}",
            "path": paths[0], "paths": paths, "bytes": group["potential_bytes"], "confidence": "Verified content",
            "risk": "review", "purpose": "These files contained identical bytes when hashed. Their different locations may still serve different purposes.",
            "evidence": [f"Full SHA-256 match: {group['hash']}", f"{len(paths)} distinct files; {group['size']:,} bytes per copy.", "Hard links are excluded from duplicate savings."],
            "consequence": "Keep at least one copy. Moving or removing another can break references or remove an intentional backup.",
            "recommendation": "Review every location and decide which copies are intentional. No copy is selected for deletion.",
        })
    generated = {}
    for file in files:
        if file.get("generated") and file["path"] not in claimed:
            key = file["generated"][0]
            generated.setdefault(key, {"kind": file["generated"][1], "files": []})["files"].append(file)
    for path, group in generated.items():
        total = sum(item["size"] for item in group["files"])
        if total < MIB:
            continue
        title, purpose, consequence = GENERATED[group["kind"]]
        members = [item["path"] for item in group["files"]]
        claimed.update(members)
        findings.append({"id": "gen-" + uid(path), "kind": "generated", "title": title, "path": path, "paths": members,
                         "bytes": total, "confidence": "Folder convention", "risk": "conditional", "purpose": purpose,
                         "evidence": [f"Recognized directory name: {group['kind']}.", f"{len(members):,} inventoried files, excluding copies already counted elsewhere.", "Regenerability has not been verified."],
                         "consequence": consequence, "recommendation": "Check the project is inactive and can be rebuilt before considering removal."})
    for file in files:
        if file["path"] in claimed:
            continue
        age = max(0, (now - file["modified"]) / DAY)
        ext = Path(file["path"]).suffix.lower()
        if ext in {".msi", ".dmg", ".pkg", ".deb", ".rpm"} and age >= 90 and file["size"] >= 10 * MIB:
            title, kind, confidence = "Older installation package", "installers", "File type & timestamp"
            recommendation = "Check whether this package is still needed for installation or recovery. Age does not prove it is unused."
        elif file["size"] >= 500 * MIB:
            title, kind, confidence = "Large file worth a look", "large", "Measured size"
            recommendation = "Review the file's purpose and backup status. Size alone is not a reason to remove it."
        else:
            continue
        description = describe_file(file)
        findings.append({"id": "file-" + file["id"], "kind": kind, "title": title, "path": file["path"], "paths": [file["path"]],
                         "bytes": file["size"], "confidence": confidence, "risk": "review", **description,
                         "evidence": [f"Logical size: {file['size']:,} bytes.", "Last modified: " + timestamp_label(file["modified"]), "Last human-opened time is unknown."],
                         "recommendation": recommendation})
    return sorted(findings, key=lambda item: item["bytes"], reverse=True)


def summarize(files: list[dict], findings: list[dict]) -> dict:
    categories = {}
    for file in files:
        entry = categories.setdefault(file["category"], {"name": file["category"], "bytes": 0, "count": 0})
        entry["bytes"] += file["size"]
        entry["count"] += 1
    return {"files": len(files), "bytes": sum(file["size"] for file in files), "findings": len(findings),
            "review_bytes": sum(item["bytes"] for item in findings),
            "duplicate_bytes": sum(item["bytes"] for item in findings if item["kind"] == "duplicates"),
            "categories": sorted(categories.values(), key=lambda item: item["bytes"], reverse=True)}
