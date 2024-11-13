from github import Github

# Authentication is defined via github.Auth
from github import Auth

# using an access token
auth = Auth.Token("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")

# First create a Github instance:

# Public Web Github
g = Github(auth=auth)

# Github Enterprise with custom hostname
#g = Github(base_url="https://github.com/SunburyAdm", auth=auth)

# Then play with your Github objects:
for repo in g.get_user().get_repos():
    print(repo.full_name)
    
repo = g.get_repo("SunburyAdm/playground")

# Get the latest commit on the specified branch
branch_name = "main"  # Specify the branch you want, e.g., "main" or "master"
latest_commit = repo.get_branch(branch_name).commit

print("Latest commit SHA:", latest_commit.sha)
print("Commit message:", latest_commit.commit.message)
print("Commit author:", latest_commit.commit.author.name)
print("Commit date:", latest_commit.commit.author.date)

# To close connections after use
g.close()