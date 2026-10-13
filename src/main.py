
import subprocess
from collections import Counter
from pathlib import PurePosixPath, PureWindowsPath


HOTSPOT_THRESHOLD = 3


def run_git_command(arguments):
    """Run a Git command and return its output."""
    try:
        result = subprocess.run(
            ["git"] + arguments,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout

    except FileNotFoundError:
        raise RuntimeError(
            "Git was not found. Install Git and ensure it is on PATH."
        )

    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or "Unknown Git error"
        raise RuntimeError(f"Git command failed: {message}")


def should_ignore_file(filename):
    """Ignore generated files and irrelevant directories."""
    normalized = filename.replace("\\", "/").strip("/")
    parts = PurePosixPath(normalized).parts
    windows_parts = PureWindowsPath(filename).parts

    all_parts = {
        part.lower()
        for part in parts + windows_parts
    }

    ignored_directories = {
        "__pycache__",
        ".venv",
        "venv",
        ".git",
        ".pytest_cache",
        "site-packages",
        "node_modules"
    }

    if all_parts & ignored_directories:
        return True

    return normalized.lower().endswith((".pyc", ".pyo"))


def get_total_commits():
    """Count commits reachable from the current HEAD."""
    output = run_git_command(["rev-list", "--count", "HEAD"])
    return int(output.strip())


def count_file_changes(log_output):
    """Count distinct commits that changed each file."""
    changes = Counter()
    files_in_commit = set()

    for line in log_output.splitlines():
        line = line.strip()

        if line.startswith("COMMIT:"):
            for filename in files_in_commit:
                changes[filename] += 1

            files_in_commit.clear()

        elif line and not should_ignore_file(line):
            files_in_commit.add(line)

    # Process files from the final commit.
    for filename in files_in_commit:
        changes[filename] += 1

    return changes


def get_file_changes():
    """Get file-change statistics from Git history."""
    output = run_git_command([
        "log",
        "--format=COMMIT:%H",
        "--name-only"
    ])

    return count_file_changes(output)


def find_hotspots(changes, threshold=HOTSPOT_THRESHOLD):
    """Find files changed in at least the threshold number of commits."""
    return {
        filename: count
        for filename, count in changes.items()
        if count >= threshold
    }


def main():
    print("\nCODEBASE ARCHAEOLOGIST")
    print("=" * 36)

    try:
        total_commits = get_total_commits()
        changes = get_file_changes()
        hotspots = find_hotspots(changes)

        print(f"\nTotal commits: {total_commits}")

        print("\nMost frequently changed files:")

        if changes:
            for filename, count in changes.most_common(10):
                print(f"  {filename}: {count} commits")
        else:
            print("No eligible file changes found.")

        print("\nCHANGE HOTSPOTS")
        print("-" * 36)

        if hotspots:
            for filename, count in sorted(
                hotspots.items(),
                key=lambda item: item[1],
                reverse=True
            ):
                print(f"  REVIEW: {filename} ({count} commits)")
        else:
            print(
                "No files meet the hotspot threshold "
                f"of {HOTSPOT_THRESHOLD} commits."
            )

        print(
            "\nNote: Frequent changes do not automatically "
            "mean a file contains bugs or is risky."
        )

    except (RuntimeError, ValueError) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()
