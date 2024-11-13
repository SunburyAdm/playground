

from github import Github

# Replace with your GitHub credentials
g = Github("sunburycabinetinvetory@gmail.com", "Sunberry24")

# Replace with your repository details
repo = g.get_repo("owner/repo_name")

# Get the latest commit on the default branch
latest_commit = repo.get_branch().commit

# Print the latest commit SHA
print(latest_commit.sha)