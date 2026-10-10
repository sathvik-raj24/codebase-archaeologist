import subprocess
from collections import Counter


def run_git_command(arguments):
    result = subprocess.run(
        ["git"] + arguments,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout


def get_total_commits():
    output = run_git_command(["rev-list", "--count", "HEAD"])
    return int(output.strip())


def get_file_changes():
    output = run_git_command([
        "log", "--pretty=format:", "--name-only"
    ])

    files = [
        filename.strip()
        for filename in output.splitlines()
        if filename.strip()
    ]

    return Counter(files)


def main():
    print("\nCODEBASE ARCHAEOLOGIST")
    print("=" * 30)

    total_commits = get_total_commits()
    changes = get_file_changes()

    print(f"\nTotal commits: {total_commits}")
    print("\nMost frequently changed files:")

    for filename, count in changes.most_common(10):
        print(f"  {filename}: {count} appearances")


if __name__ == "__main__":
    main()