#!/usr/bin/env python3
"""Update a Markdown "Addressed issues" section from a GitHub milestone."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_SECTION = "Addressed issues"


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Fetch issues for one GitHub repo milestone and optionally update a Markdown section."
	)
	parser.add_argument("repo", help="GitHub repository in owner/name form, for example gemc/pygemc.")
	parser.add_argument("milestone", type=int, help="GitHub milestone number in that repository.")
	parser.add_argument(
		"--file",
		type=Path,
		help="Markdown file to update. If omitted, updates the latest versioned file in ./releases.",
	)
	parser.add_argument(
		"--section",
		default=DEFAULT_SECTION,
		help=f"Markdown section to replace. Default: {DEFAULT_SECTION!r}.",
	)
	parser.add_argument(
		"--state",
		choices=("open", "closed", "all"),
		default="all",
		help="Issue state to fetch. Default: all.",
	)
	parser.add_argument(
		"--token-env",
		default="GITHUB_TOKEN",
		help="Environment variable holding a GitHub token. Default: GITHUB_TOKEN.",
	)
	return parser


def main(argv: list[str] | None = None) -> int:
	args = build_parser().parse_args(argv)
	validate_repo(args.repo)

	token = os.environ.get(args.token_env)
	issues = fetch_milestone_issues(args.repo, args.milestone, args.state, token)
	lines = format_issues(args.repo, issues)

	default_file = default_release_file(args.repo)
	if args.file is None and default_file is None:
		print("\n".join(lines))
		if Path("releases").is_dir():
			print(
				f"Not updating ./releases because this checkout does not appear to be {args.repo}. "
				"Use --file to override.",
				file=sys.stderr,
			)
		return 0

	path = args.file or default_file
	print(f"repo={args.repo} milestone={args.milestone} release_file={path}")
	update_markdown_section(path, args.section, lines)
	print(f"Updated {path} with {len(issues)} issue(s) from {args.repo} milestone {args.milestone}.")
	return 0


def validate_repo(repo: str) -> None:
	if not re.fullmatch(r"[^/\s]+/[^/\s]+", repo):
		raise SystemExit("repo must be in owner/name form, for example gemc/pygemc")


def default_release_file(repo: str) -> Path | None:
	candidates = [Path.cwd(), Path(__file__).resolve().parents[1]]
	for root in candidates:
		if current_repo_matches(root, repo) and (root / "releases").is_dir():
			return latest_release_file(root / "releases")
	return None


def current_repo_matches(root: Path, repo: str) -> bool:
	git_dir = root / ".git"
	if not git_dir.exists():
		return False

	try:
		import subprocess

		result = subprocess.run(
			["git", "remote", "get-url", "origin"],
			check=True,
			capture_output=True,
			text=True,
			cwd=root,
		)
	except Exception:
		return False

	remote = result.stdout.strip().removesuffix(".git")
	return remote.endswith(f":{repo}") or remote.endswith(f"/{repo}")


def fetch_milestone_issues(repo: str, milestone: int, state: str, token: str | None) -> list[dict]:
	issues: list[dict] = []
	page = 1

	while True:
		query = urlencode(
			{
				"milestone": milestone,
				"state": state,
				"per_page": 100,
				"page": page,
			}
		)
		url = f"https://api.github.com/repos/{repo}/issues?{query}"
		page_items = read_json(url, token)
		if not page_items:
			break

		issues.extend(issue for issue in page_items if "pull_request" not in issue)
		if len(page_items) < 100:
			break
		page += 1

	return sorted(issues, key=lambda issue: issue["number"])


def read_json(url: str, token: str | None) -> list[dict]:
	headers = {
		"Accept": "application/vnd.github+json",
		"X-GitHub-Api-Version": "2022-11-28",
		"User-Agent": "gemc-release-notes",
	}
	if token:
		headers["Authorization"] = f"Bearer {token}"

	request = Request(url, headers=headers)
	try:
		with urlopen(request, timeout=30) as response:
			return json.loads(response.read().decode("utf-8"))
	except HTTPError as exc:
		message = exc.read().decode("utf-8", errors="replace")
		raise SystemExit(f"GitHub API error {exc.code}: {message}") from exc
	except URLError as exc:
		raise SystemExit(f"Could not reach GitHub API: {exc.reason}") from exc


def format_issues(repo: str, issues: list[dict]) -> list[str]:
	if not issues:
		return ["- No issues assigned to this milestone."]

	return [
		f"- [Issue #{issue['number']}](https://github.com/{repo}/issues/{issue['number']}): {issue['title']}"
		for issue in issues
	]


def latest_release_file(releases_dir: Path) -> Path:
	candidates = []
	for path in releases_dir.glob("*.md"):
		version = release_version(path)
		if version is not None:
			candidates.append((version, path))

	if not candidates:
		raise SystemExit(f"No versioned release notes found in {releases_dir}. Use --file to select a file.")

	return max(candidates, key=lambda item: item[0])[1]


def release_version(path: Path) -> tuple[int, ...] | None:
	match = re.fullmatch(r"v?(\d+(?:\.\d+)*)\.md", path.name)
	if match is None:
		return None
	return tuple(int(part) for part in match.group(1).split("."))


def update_markdown_section(path: Path, section: str, replacement_lines: list[str]) -> None:
	text = path.read_text()
	heading = f"## {section}"
	pattern = re.compile(
		rf"(^##[ \t]+{re.escape(section)}[ \t]*\n)(.*?)(?=^(?:<br/>\s*\n\s*)?##[ \t]+|\Z)",
		re.MULTILINE | re.DOTALL,
	)

	def replace(match: re.Match[str]) -> str:
		return match.group(1) + "\n" + "\n".join(replacement_lines) + "\n\n"

	new_text, count = pattern.subn(replace, text, count=1)
	if count == 0:
		append = f"\n<br/>\n\n{heading}\n\n" + "\n".join(replacement_lines) + "\n"
		new_text = text.rstrip() + append

	path.write_text(new_text)


if __name__ == "__main__":
	sys.exit(main())
