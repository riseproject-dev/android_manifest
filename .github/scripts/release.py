#!/usr/bin/env python3
"""Build the parts of a RISE release that come from its pinned manifests.

manifests  pin the manifests of this repository to the revisions of a
           nightly: its default.xml, then the kernel and bootloader
           manifests that the prebuilt updates committed in device/rise and
           vendor/rise
notes      write the release notes: those of the previous release with its
           version replaced, and the changes since it
tag        tag every riseproject-dev project of the pinned manifests, and
           the sources of the Mesa and WebView prebuilts, with one tag per
           board when the boards build different revisions
repos      list the riseproject-dev repositories that a release may tag

The nightly manifests are written on the AOSP builder, which runs code from
every synced project, and users sync the release manifests. So only the
revisions of the nightly manifests are used, once checked: every manifest
of a release is a manifest of this repository with these revisions.
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OWNER = "riseproject-dev"
RISE = f"https://github.com/{OWNER}/"
SHA = re.compile(r"[0-9a-f]{40}")
# Commits listed per project before the notes link to the full comparison.
MAX_COMMITS = 30

# Manifest, title in the notes, board, and where the prebuilt updates keep it.
MANIFESTS = [
    ("default.xml", "Android tree", None, None),
    ("kernel-spacemit.xml", "K3 kernel", "k3",
     ("android_device_rise", "spacemit/kernel/mainline")),
    ("kernel-alibaba.xml", "A210 kernel", "a210",
     ("android_device_rise", "alibaba/kernel/mainline")),
    ("bootloader-spacemit.xml", "K3 bootloaders", "k3",
     ("android_vendor_rise", "spacemit/k3/bootloader")),
    ("bootloader-alibaba.xml", "A210 bootloaders", "a210",
     ("android_vendor_rise", "alibaba/a210/bootloader")),
]

# Source, branch, board and path in device/rise of the prebuilts built from
# a repository that no manifest lists.
PREBUILTS = [
    ("mesa", "android-17-imagination", "k3", "spacemit/k3/mesa/lib64"),
    ("mesa", "android-17-imagination", "a210", "alibaba/a210/mesa/lib64"),
    ("android-webview-riscv64", "android-17", None, "common/webview/SystemWebView64.apk"),
]


def gh(*args):
    return subprocess.run(["gh", "api", *args], check=True, capture_output=True,
                          text=True).stdout


def key(project):
    return project.get("name"), project.get("path") or project.get("name")


def read(path):
    """Return the {(name, path): (URL, revision)} of the projects of a
    manifest of this repository, or of a manifest that pins one."""
    root = ET.parse(path).getroot()
    remotes = {r.get("name"): r for r in root.iter("remote")}
    default = root.find("default")
    default = {} if default is None else default.attrib
    result = {}
    for element in root:
        if element.tag == "project":
            remote = remotes.get(element.get("remote") or default.get("remote"))
            result[key(element)] = (
                None if remote is None else remote.get("fetch"),
                element.get("revision") or (remote is not None and remote.get("revision"))
                or default.get("revision"))
        elif element.tag == "remove-project":
            result = {k: v for k, v in result.items()
                      if k[0] != element.get("name") or element.get("path") not in (None, k[1])}
    return result


def projects(path):
    """Return the {name: revision} of the RISE and of the other projects."""
    rise, other = {}, {}
    for (name, _), (fetch, revision) in read(path).items():
        (rise if fetch == RISE else other)[name] = revision
    return rise, other


def on_gitiles_branch(fetch, project, revision, branch):
    """Tell whether a commit is on a branch of a googlesource project."""
    url = f"{fetch}{project}/+log/refs/heads/{branch}..{revision}?format=JSON&n=1"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url) as response:
                # Gitiles prefixes its JSON with a line that guards against XSSI.
                return json.loads(response.read().decode().split("\n", 1)[1])["log"] == []
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            if error.code != 429 or attempt == 4:
                raise
            time.sleep(30 * (attempt + 1))


def check(name, project, fetch, branch, revision, before):
    """Check a revision that a nightly pins. googlesource also serves the
    commits of unmerged Gerrit changes, which anyone can upload: the other
    projects are checked unless the previous release, which before maps to
    its revisions, already had this one. Without a previous release, only
    the RISE projects are checked."""
    if not SHA.fullmatch(revision or ""):
        sys.exit(f"{name} pins {project} to '{revision}', not to a commit.")
    if SHA.fullmatch(branch or ""):
        on_branch = revision == branch
    elif fetch == RISE:
        status = json.loads(gh(f"repos/{OWNER}/{project}/compare/"
                               f"{revision}...{branch}?per_page=1"))["status"]
        on_branch = status in ("identical", "ahead")
    elif before is None or before.get(project) == revision:
        on_branch = True
    else:
        on_branch = (fetch.endswith(".googlesource.com/")
                     and on_gitiles_branch(fetch, project, revision, branch))
    if not on_branch:
        sys.exit(f"{name} pins {project} to {revision}, which is not on {branch}.")


def pin(name, pinned, trusted, previous):
    """Replace the pinned manifest name with the one of this repository,
    pinned to its checked revisions."""
    revisions = {k: revision for k, (_, revision) in read(pinned / name).items()}
    known = read(trusted / name)
    before = None
    if previous:
        before = {k[0]: revision for k, (_, revision) in
                  (read(previous / name) if (previous / name).exists() else {}).items()}
    tree = ET.parse(trusted / name)
    for element in tree.getroot().iter("project"):
        # Projects that a <remove-project> drops, and those out of the synced
        # groups, which repo does not pin, keep their branch.
        if key(element) not in known:
            continue
        fetch, branch = known[key(element)]
        revision = revisions.get(key(element))
        if revision in (None, branch):
            continue
        check(name, key(element)[0], fetch, branch, revision, before)
        element.set("revision", revision)
        if not SHA.fullmatch(branch):
            element.set("upstream", branch)
    tree.write(pinned / name, encoding="UTF-8", xml_declaration=True)


def prebuilt_source(device, project, path):
    """Return the commit of project that the prebuilts at path were built
    from in device/rise at revision device, as their last update lists it,
    or None when it does not."""
    update = json.loads(gh(f"repos/{OWNER}/android_device_rise/commits"
                           f"?sha={device}&path={path}&per_page=1"))
    m = re.search(r"^\s*(?:HEAD|Commit): ([0-9a-f]{7,40})\b",
                  update[0]["commit"]["message"] if update else "", re.M)
    return m and json.loads(gh(f"repos/{OWNER}/{project}/commits/{m.group(1)}"))["sha"]


def prebuilt_sources(pinned):
    """Return the checked {(project, board): revision} of the prebuilt
    sources of the device/rise revision of the pinned default.xml."""
    device = projects(pinned / "default.xml")[0]["android_device_rise"]
    result = {}
    for project, branch, board, path in PREBUILTS:
        revision = prebuilt_source(device, project, path)
        if revision is None:
            sys.exit(f"android_device_rise does not tell which {project} commit "
                     f"built {path} at {device}.")
        check("android_device_rise", project, RISE, branch, revision, None)
        result[project, board] = revision
    return result


def manifests(args):
    pin("default.xml", args.dir, args.trusted, args.previous)
    rise, _ = projects(args.dir / "default.xml")
    for name, _, _, (repo, path) in MANIFESTS[1:]:
        try:
            content = gh("-H", "Accept: application/vnd.github.raw+json",
                         f"repos/{OWNER}/{repo}/contents/{path}/{name}?ref={rise[repo]}")
        except subprocess.CalledProcessError:
            sys.exit(f"{repo} has no {path}/{name} at {rise[repo]}: "
                     "rebuild these prebuilts before releasing.")
        (args.dir / name).write_text(content)
        pin(name, args.dir, args.trusted, args.previous)
    prebuilt_sources(args.dir)


def sources(body):
    """Return the source heads that a prebuilt update commit lists."""
    project, result = None, []
    for line in body.splitlines():
        if m := re.match(r"- Project: (.+):$", line):
            project = m.group(1)
        elif line.startswith("HEAD: ") and project:
            result.append(f"{project}: {line[6:]}")
    return result


def commits(name, old, new):
    compare = f"https://github.com/{OWNER}/{name}/compare/{old[:12]}...{new[:12]}"
    data = json.loads(gh(f"repos/{OWNER}/{name}/compare/{old}...{new}?per_page=100"))
    # The CI changes do not change what the release holds, and only the last
    # of the prebuilt updates of a path is shipped.
    shown, updates = [], set()
    for commit in reversed(data["commits"]):
        message = commit["commit"]["message"]
        if message.startswith("ci: "):
            continue
        if commit["commit"]["author"]["name"].endswith("[bot]"):
            if message.splitlines()[0] in updates:
                continue
            updates.add(message.splitlines()[0])
        shown.append(commit)
    if not shown:
        return []
    total = data["total_commits"]
    lines = [f"- **{name}** ([{total} commit{'s' if total > 1 else ''}]({compare}))"]
    for commit in shown[:MAX_COMMITS]:
        message = commit["commit"]["message"]
        lines.append(f"  - {message.splitlines()[0]} (`{commit['sha'][:12]}`)")
        if commit["commit"]["author"]["name"].endswith("[bot]"):
            lines += [f"    - {s}" for s in sources(message)]
    if len(shown) > MAX_COMMITS:
        lines.append(f"  - and {len(shown) - MAX_COMMITS} more")
    return lines


def changes(previous, current, since):
    lines = [f"## Changes since {since}", ""]
    for name, title, _, _ in MANIFESTS:
        old_rise, old_other = projects(previous / name) if (previous / name).exists() else ({}, {})
        new_rise, new_other = projects(current / name)
        entries = []
        for project, revision in sorted(new_rise.items()):
            old = old_rise.get(project)
            if old == revision:
                continue
            if old is None:
                entries.append(f"- **{project}**: new, at `{revision[:12]}`")
            elif not SHA.fullmatch(old):
                entries.append(f"- **{project}**: now at `{revision[:12]}`, not pinned in {since}")
            else:
                entries += commits(project, old, revision)
        updated = sum(SHA.fullmatch(r or "") is not None and old_other.get(p) != r
                      for p, r in new_other.items())
        if updated:
            entries.append(f"- {updated} other projects updated")
        if entries:
            lines += [f"### {title}", "", *entries, ""]
    old_device = (projects(previous / "default.xml")[0].get("android_device_rise")
                  if (previous / "default.xml").exists() else None)
    entries, seen = [], set()
    for (project, board), revision in prebuilt_sources(current).items():
        path = next(p for n, _, b, p in PREBUILTS if (n, b) == (project, board))
        old = old_device and prebuilt_source(old_device, project, path)
        if old == revision or (project, old, revision) in seen:
            continue
        seen.add((project, old, revision))
        if old is None:
            entries.append(f"- **{project}**: now at `{revision[:12]}`, not recorded in {since}")
        else:
            entries += commits(project, old, revision)
    if entries:
        lines += ["### Mesa and WebView", "", *entries, ""]
    return lines


def notes(args):
    since = args.previous_tag.removeprefix(args.branch + "-")
    version = args.tag.removeprefix(args.branch + "-")
    body = (args.previous / "notes.md").read_text()
    body = re.sub(rf"(?<![0-9A-Za-z.]){re.escape(since)}(?![0-9])", version, body)
    section = "\n".join(changes(args.previous, args.dir, since))
    # The changes come right before the feature table, or the sources.
    for heading in ("## What works", "## Sources"):
        if heading in body:
            body = body.replace(heading, section + "\n" + heading, 1)
            break
    else:
        body += "\n\n" + section
    print(body)


def tag(args):
    if not re.fullmatch(rf"{re.escape(args.branch)}-v[0-9]+\.[0-9]+", args.tag):
        sys.exit(f"Unexpected release tag '{args.tag}'.")
    # {project: {board: revision}}, the Android tree counting for any board.
    revisions = {}
    for name, _, board, _ in MANIFESTS:
        pin(name, args.dir, args.trusted, None)
        for project, revision in projects(args.dir / name)[0].items():
            revisions.setdefault(project, {})[board] = revision
    for (project, board), revision in prebuilt_sources(args.dir).items():
        revisions.setdefault(project, {})[board] = revision
    for project, boards in sorted(revisions.items()):
        if len(set(boards.values())) == 1:
            targets = {args.tag: next(iter(boards.values()))}
        else:
            targets = {args.tag if board is None else f"{args.tag}-{board}": revision
                       for board, revision in boards.items()}
        for name, revision in targets.items():
            create_tag(project, name, revision)


def create_tag(project, name, revision):
    try:
        existing = json.loads(gh(f"repos/{OWNER}/{project}/git/ref/tags/{name}"))
    except subprocess.CalledProcessError:
        existing = None
    if existing:
        target = existing["object"]
        if target["type"] == "tag":
            target = json.loads(gh(f"repos/{OWNER}/{project}/git/tags/{target['sha']}"))["object"]
        if target["sha"] != revision:
            sys.exit(f"{project} already has {name} at {target['sha']}, not {revision}.")
        print(f"{project}: {name} already at {revision[:12]}")
        return
    tag_object = json.loads(gh("-X", "POST", f"repos/{OWNER}/{project}/git/tags",
                               "-f", f"tag={name}", "-f", f"message={name}",
                               "-f", f"object={revision}", "-f", "type=commit"))
    gh("-X", "POST", f"repos/{OWNER}/{project}/git/refs",
       "-f", f"ref=refs/tags/{name}", "-f", f"sha={tag_object['sha']}")
    print(f"{project}: tagged {name} at {revision[:12]}")


def repos(args):
    names = set()
    for name, _, _, _ in MANIFESTS:
        names |= projects(args.trusted / name)[0].keys()
    names |= {project for project, _, _, _ in PREBUILTS}
    print(",".join(sorted(names)))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["manifests", "notes", "tag", "repos"])
    parser.add_argument("--branch", default="android-17")
    parser.add_argument("--dir", type=Path, help="pinned manifests of the release")
    parser.add_argument("--trusted", type=Path,
                        help="checkout of this repository (manifests, tag, repos)")
    parser.add_argument("--tag", help="release tag (notes, tag)")
    parser.add_argument("--previous-tag", help="tag of the previous release (notes)")
    parser.add_argument("--previous", type=Path,
                        help="manifests and notes.md of the previous release (manifests, notes)")
    args = parser.parse_args()
    {"manifests": manifests, "notes": notes, "tag": tag, "repos": repos}[args.command](args)


if __name__ == "__main__":
    main()
