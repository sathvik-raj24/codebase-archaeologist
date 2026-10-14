
import subprocess
from collections import Counter
from pathlib import PurePosixPath, PureWindowsPath


HOTSPOT_THRESHOLD = 3
CO_CHANGE_THRESHOLD = 2


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

    # Process the final commit.
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
    """Find files changed in at least the specified number of commits."""
    return {
        filename: count
        for filename, count in changes.items()
        if count >= threshold
    }


def find_co_changed_files(
    log_output,
    min_shared_commits=CO_CHANGE_THRESHOLD
):
    """Find file pairs that change together in multiple commits."""
    pair_counts = Counter()
    files_in_commit = set()

    def record_pairs(files):
        ordered_files = sorted(files)

        for i in range(len(ordered_files)):
            for j in range(i + 1, len(ordered_files)):
                pair = (ordered_files[i], ordered_files[j])
                pair_counts[pair] += 1

    for line in log_output.splitlines():
        line = line.strip()

        if line.startswith("COMMIT:"):
            record_pairs(files_in_commit)
            files_in_commit.clear()

        elif line and not should_ignore_file(line):
            files_in_commit.add(line)

    # Process the final commit.
    record_pairs(files_in_commit)

    return {
        pair: count
        for pair, count in pair_counts.items()
        if count >= min_shared_commits
    }


def get_co_changed_files(
    min_shared_commits=CO_CHANGE_THRESHOLD
):
    """Analyze Git history for files that change together."""
    output = run_git_command([
        "log",
        "--format=COMMIT:%H",
        "--name-only"
    ])

    return find_co_changed_files(
        output,
        min_shared_commits=min_shared_commits
    )


def generate_repository_summary(
    total_commits, changes, hotspots, co_changes
):
    """Generate a high-level summary of repository activity."""
    return {
        "total_commits": total_commits,
        "files_changed": len(changes),
        "hotspots": len(hotspots),
        "co_change_relationships": len(co_changes),
    }


def main():
    print("\nCODEBASE ARCHAEOLOGIST")
    print("=" * 40)

    try:
        total_commits = get_total_commits()
        changes = get_file_changes()
        hotspots = find_hotspots(changes)
        co_changes = get_co_changed_files()

        summary = generate_repository_summary(
            total_commits, changes, hotspots, co_changes
        )

        print("\nREPOSITORY SUMMARY")
        print("-" * 40)
        print(f"Commits analyzed: {summary['total_commits']}")
        print(f"Distinct files changed: {summary['files_changed']}")
        print(f"Change hotspots: {summary['hotspots']}")
        print(
            "Recurring co-change relationships: "
            f"{summary['co_change_relationships']}"
        )

        print("\nMOST FREQUENTLY CHANGED FILES")
        print("-" * 40)

        if changes:
            for filename, count in changes.most_common(10):
                print(f"  {filename}: {count} commits")
        else:
            print("No eligible file changes found.")

        print("\nCHANGE HOTSPOTS")
        print("-" * 40)

        if hotspots:
            for filename, count in sorted(
                hotspots.items(),
                key=lambda item: item[1],
                reverse=True
            ):
                print(f"  REVIEW: {filename} ({count} commits)")
        else:
            print(
                f"No files meet the threshold of "
                f"{HOTSPOT_THRESHOLD} commits."
            )

        print("\nFILES THAT CHANGE TOGETHER")
        print("-" * 40)

        if co_changes:
            for (file_a, file_b), count in sorted(
                co_changes.items(),
                key=lambda item: item[1],
                reverse=True
            )[:10]:
                print(
                    f"  {file_a} <-> {file_b}: "
                    f"{count} shared commits"
                )
        else:
            print(
                "No file pairs found that changed together "
                f"in at least {CO_CHANGE_THRESHOLD} commits."
            )

        print(
            "\nNote: Frequent changes and co-change patterns "
            "are investigation clues, not proof of bugs or "
            "direct dependencies."
        )

    except (RuntimeError, ValueError) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()
