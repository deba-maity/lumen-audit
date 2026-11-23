"""Bounded filesystem inventory with optional content hashing. No subprocesses or writes."""
from __future__ import annotations

import hashlib
import os
import stat
import threading
import time
from collections import defaultdict
from pathlib import Path

from .rules import GIB, MIB, PROTECTED_NAMES, category, describe_file, findings_for, generated_info, summarize, uid

MAX_FILES = 100_000
MAX_ENTRIES = 200_000
MAX_HASH_FILE = 512 * MIB
MAX_HASH_BYTES = 2 * GIB
# Offline / recall-on-open / recall-on-data-access. Do not hydrate cloud files.
CLOUD_ATTRIBUTES = 0x1000 | 0x40000 | 0x400000
REPARSE_ATTRIBUTE = 0x400
SENSITIVE_NAMES = {".env", "credentials", "id_rsa", "id_ed25519", "pagefile.sys", "hiberfil.sys", "swapfile.sys"}


def unsafe_entry(path: Path, info: os.stat_result) -> str | None:
    attrs = getattr(info, "st_file_attributes", 0)
    if stat.S_ISLNK(info.st_mode) or attrs & REPARSE_ATTRIBUTE:
        return "Link, junction, or reparse point (not followed)"
    if attrs & CLOUD_ATTRIBUTES:
        return "Cloud-only or offline item (not downloaded)"
    unix_system = {"proc", "sys", "dev", "etc", "bin", "sbin", "lib", "lib64", "usr"}
    protected = path.name.lower() in PROTECTED_NAMES
    if path.name.lower() in unix_system:
        protected = os.name != "nt" and path.parent == Path(path.anchor)
    if protected:
        return "Protected system, credential, or version-control directory"
    if path.name.lower() in SENSITIVE_NAMES or path.name.lower().startswith(".env."):
        return "Sensitive or system-managed file"
    return None


def validate_roots(raw: list[str], excluded: Path | None = None) -> list[Path]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= 8:
        raise ValueError("Choose between one and eight local folders.")
    roots = []
    for value in raw:
        if not isinstance(value, str) or not value.strip() or len(value) > 4096:
            raise ValueError("Each folder must be a valid absolute local path.")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        if value.startswith(("\\\\", "//")):
            raise ValueError("Network shares and device paths are not supported. Choose a local folder.")
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            raise ValueError("Use an absolute folder path, for example C:\\Users\\you\\Downloads.")
        if os.name == "nt":
            import ctypes
            # Reject mapped network drives before any filesystem lookup.
            if ctypes.windll.kernel32.GetDriveTypeW(candidate.anchor) == 4:
                raise ValueError("Mapped network drives are not supported. Choose a local disk.")
        # Check every ancestor before resolving: resolution must not silently follow a junction.
        for part in reversed([candidate, *candidate.parents]):
            info = part.lstat()
            reason = unsafe_entry(part, info)
            if reason:
                raise ValueError(f"Cannot scan {part.name or part}: {reason}.")
        if not candidate.is_dir():
            raise ValueError(f"Not a folder: {candidate}")
        candidate = candidate.resolve()
        if excluded and (candidate == excluded or excluded in candidate.parents):
            raise ValueError("Lumen's own state folder is excluded from scanning.")
        if not any(candidate == root or root in candidate.parents for root in roots):
            roots = [root for root in roots if candidate not in root.parents]
            roots.append(candidate)
    return roots


def installed_apps(cancel=None) -> tuple[list[dict], list[str]]:
    """Read registry metadata only; never use Win32_Product, which can trigger repairs."""
    if os.name != "nt":
        return [], ["Installed-app inventory is currently available on Windows only."]
    import winreg
    apps, warnings, seen = [], [], set()
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            if cancel is not None and cancel.is_set():
                raise ScanCancelled()
            try:
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | view) as key:
                    for index in range(winreg.QueryInfoKey(key)[0]):
                        if cancel is not None and cancel.is_set():
                            raise ScanCancelled()
                        try:
                            with winreg.OpenKey(key, winreg.EnumKey(key, index)) as app_key:
                                def read(name):
                                    try:
                                        return str(winreg.QueryValueEx(app_key, name)[0])[:1000]
                                    except OSError:
                                        return ""
                                name, version, publisher = read("DisplayName"), read("DisplayVersion"), read("Publisher")
                                if not name or (name, version, publisher) in seen or read("SystemComponent") == "1":
                                    continue
                                seen.add((name, version, publisher))
                                apps.append({"name": name, "version": version, "publisher": publisher, "location": read("InstallLocation"),
                                             "service_date": read("InstallDate"), "last_used": None,
                                             "source": "Windows Uninstall registry (declared metadata)"})
                        except OSError:
                            continue
            except FileNotFoundError:
                continue
            except OSError:
                warnings.append("Some installed-app registry entries could not be read.")
    return sorted(apps, key=lambda app: app["name"].lower()), sorted(set(warnings))


class ScanCancelled(Exception):
    pass


def scan(roots: list[Path], *, cancel: threading.Event, progress, hash_duplicates=False,
         include_apps=False, excluded: Path | None = None, max_files=MAX_FILES,
         max_entries=MAX_ENTRIES, hash_budget=MAX_HASH_BYTES) -> dict:
    started = time.time()
    monotonic_started = time.monotonic()
    files, skipped, warnings = [], [], []
    skip_count, entry_count, directories = 0, 0, 0
    seen_inodes = set()
    bounded = False

    def check_cancel():
        if cancel.is_set():
            raise ScanCancelled()

    def skip(path, reason):
        nonlocal skip_count
        skip_count += 1
        if len(skipped) < 500:
            skipped.append({"path": str(path), "reason": reason})

    for root in roots:
        stack = [root]
        while stack:
            check_cancel()
            directory = stack.pop()
            try:
                reason = unsafe_entry(directory, directory.lstat())
                if reason:
                    skip(directory, reason)
                    continue
                directories += 1
                with os.scandir(directory) as entries:
                    for entry in entries:
                        check_cancel()
                        entry_count += 1
                        if len(files) >= max_files or entry_count > max_entries:
                            bounded = True
                            break
                        path = Path(entry.path)
                        try:
                            info = entry.stat(follow_symlinks=False)
                            reason = unsafe_entry(path, info)
                            if excluded and (path == excluded or excluded in path.parents):
                                reason = "Lumen's local state (excluded)"
                            if reason:
                                skip(path, reason)
                                continue
                            if stat.S_ISDIR(info.st_mode):
                                stack.append(path)
                                continue
                            if not stat.S_ISREG(info.st_mode):
                                skip(path, "Special file (not read)")
                                continue
                            # Windows DirEntry.stat can omit file IDs (st_ino/st_dev).
                            # A full lstat supplies stable identity for hard links and hashing.
                            if os.name == "nt":
                                info = path.lstat()
                                reason = unsafe_entry(path, info)
                                if reason or not stat.S_ISREG(info.st_mode):
                                    skip(path, reason or "File changed during inventory")
                                    continue
                            identity = (info.st_dev, info.st_ino)
                            if info.st_ino and identity in seen_inodes:
                                skip(path, "Hard link already inventoried; not counted twice")
                                continue
                            if info.st_ino:
                                seen_inodes.add(identity)
                            relative = path.relative_to(root)
                            files.append({"id": uid(str(path)), "name": path.name, "path": str(path), "root": str(root),
                                          "relative": str(relative), "folder": relative.parts[0] if len(relative.parts) > 1 else "Files in root",
                                          "size": info.st_size, "modified": info.st_mtime, "accessed": info.st_atime, "last_opened": None,
                                          "category": category(path), "generated": generated_info(path, root),
                                          "identity": [info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size]})
                            if len(files) % 200 == 0:
                                progress({"phase": "inventory", "files": len(files), "folders": directories, "skipped": skip_count})
                        except (OSError, ValueError):
                            skip(path, "Unavailable or changed during scan")
            except OSError:
                skip(directory, "Permission denied or folder unavailable")
            if bounded:
                break
        if bounded:
            break
    if bounded:
        warnings.append(f"Inventory limit reached ({max_files:,} files / {max_entries:,} entries). This is a partial snapshot; choose smaller folders for more detail.")

    duplicate_groups, hashed_bytes, hashed_files = [], 0, 0
    hash_skipped = 0
    if hash_duplicates:
        sizes = defaultdict(list)
        for file in files:
            if 0 < file["size"] <= MAX_HASH_FILE:
                sizes[file["size"]].append(file)
            elif file["size"] > MAX_HASH_FILE:
                hash_skipped += 1
        for size, candidates in sorted(sizes.items()):
            if len(candidates) < 2:
                continue
            matches = defaultdict(list)
            for file in candidates:
                check_cancel()
                if hashed_bytes + size > hash_budget:
                    hash_skipped += 1
                    continue
                path = Path(file["path"])
                try:
                    info = path.lstat()
                    if unsafe_entry(path, info) or [info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size] != file["identity"]:
                        skip(path, "Changed before duplicate verification")
                        continue
                    # Recheck parents to avoid following a directory replaced by a link.
                    if any(unsafe_entry(parent, parent.lstat()) for parent in path.parents):
                        skip(path, "Parent became protected or linked before hashing")
                        continue
                    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
                    descriptor = os.open(path, flags)
                    digest = hashlib.sha256()
                    with os.fdopen(descriptor, "rb") as stream:
                        opened = os.fstat(stream.fileno())
                        if [opened.st_dev, opened.st_ino, opened.st_mtime_ns, opened.st_size] != file["identity"] or not stat.S_ISREG(opened.st_mode):
                            skip(path, "File identity changed before hashing")
                            continue
                        remaining = size
                        while remaining:
                            check_cancel()
                            block = stream.read(min(MIB, remaining))
                            if not block:
                                raise ValueError("File shrank during hashing")
                            remaining -= len(block)
                            hashed_bytes += len(block)
                            digest.update(block)
                        after = os.fstat(stream.fileno())
                        if after.st_mtime_ns != opened.st_mtime_ns or after.st_size != opened.st_size:
                            skip(path, "Changed during duplicate verification")
                            continue
                    hashed_files += 1
                    matches[digest.hexdigest()].append(file)
                    progress({"phase": "hashing", "files": len(files), "hashed_files": hashed_files, "hashed_bytes": hashed_bytes, "skipped": skip_count})
                except (OSError, ValueError):
                    skip(path, "Could not verify duplicate content within read budget")
            for digest, members in matches.items():
                if len(members) > 1:
                    duplicate_groups.append({"id": digest[:20], "hash": digest, "size": size, "files": members,
                                             "potential_bytes": size * (len(members) - 1)})
    if hash_skipped:
        warnings.append(f"{hash_skipped:,} files not hashed because of the 512 MiB per-file or 2 GiB total read limit. Duplicate results are not exhaustive.")
    check_cancel()
    apps = []
    if include_apps:
        progress({"phase": "applications", "files": len(files), "skipped": skip_count})
        apps, app_warnings = installed_apps(cancel)
        warnings.extend(app_warnings)
    findings = findings_for(files, duplicate_groups, started)
    for file in files:
        file.pop("identity", None)
        file.update(describe_file(file))
    report = {"id": uid(f"{started}-{roots}"), "name": "Local snapshot", "demo": False, "created": started,
              "duration": round(time.monotonic() - monotonic_started, 2), "roots": [str(root) for root in roots], "files": files,
              "findings": findings, "duplicates": duplicate_groups, "apps": apps, "skipped": skipped, "warnings": warnings,
              "coverage": {"skipped": skip_count, "directories": directories, "entries": entry_count, "limited": bounded,
                           "hashing": hash_duplicates, "hashed_files": hashed_files, "hashed_bytes": hashed_bytes,
                           "hash_skipped": hash_skipped, "apps_requested": include_apps},
              "summary": summarize(files, findings)}
    return report
