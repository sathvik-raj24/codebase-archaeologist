
import subprocess
from collections import Counter
from pathlib import PurePosixPath, PureWindowsPath


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
    """Return True for generated or irrelevant files."""
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

    if normalized.lower().endswith((".pyc", ".pyo")):
        return True

    return False


def get_total_commits():
    """Count commits reachable from the current HEAD."""
    output = run_git_command([
        "rev-list",
        "--count",
        "HEAD"
    ])

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

    # Process the final commit in the log.
    for filename in files_in_commit:
        changes[filename] += 1

    return changes


def get_file_changes():
    """Retrieve file names from Git commit history."""
    output = run_git_command([
        "log",
        "--format=COMMIT:%H",
        "--name-only"
    ])

    return count_file_changes(output)


def main():
    print("\nCODEBASE ARCHAEOLOGIST")
    print("=" * 36)

    try:
        total_commits = get_total_commits()
        changes = get_file_changes()

        print(f"\nTotal commits: {total_commits}")
        print("\nMost frequently changed files:")

        if not changes:
            print("No eligible file changes found.")
            return

        for filename, count in changes.most_common(10):
            print(f"  {filename}: {count} commits")

        print(
            "\nNote: Each file is counted at most once "
            "per commit. This is not a lines-changed metric."
        )

    except (RuntimeError, ValueError) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()
