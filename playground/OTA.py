from github import Github

# Authentication is defined via github.Auth
from github import Auth

import json
from datetime import datetime
from git import Repo
import os

# using an access token
auth = Auth.Token("")

# First create a Github instance:

# Public Web Github
g = Github(auth=auth)

# Then play with your Github objects:
#for repo in g.get_user().get_repos():
#    print(repo.full_name)
    
repo = g.get_repo("SunburyAdm/playground")

# Get the latest commit on the specified branch
branch_name = "main"  # Specify the branch you want, e.g., "main" or "master"
latest_commit = repo.get_branch(branch_name).commit

#print("Latest commit SHA:", latest_commit.sha)
#print("Commit message:", latest_commit.commit.message)
#print("Commit author:", type(latest_commit.commit.author.name))
#print("Commit date:", type(latest_commit.commit.author.date))


#Open json file and extract information
with open('commit_info.json', 'r') as file:
    data = json.load(file)

# Parse date strings into datetime objects
date1 = datetime.fromisoformat(data["date"])
date2 = datetime.fromisoformat(str(latest_commit.commit.author.date))

# Compare dates
if date2 > date1:
    print("New changes incoming")
    
    ### close tkinter windows for updating ####
    
    
    ###########################################
    
    
    ###### fetch and merge remote repository
    current_directory = os.getcwd()
    
    local_repo = Repo(current_directory)
    
    # Ensure the repository is clean
    assert not local_repo.bare
    
    # Fetch updates from the remote
    print("Fetching latest changes from origin...")
    origin = local_repo.remotes.origin
    origin.fetch()
    
    # Merge fetched changes into the current branch
    # Checkout to the branch you want to update
    local_repo.git.checkout(branch_name)
    
    # Perform the merge
    try:
        local_repo.git.merge(f"origin/{branch_name}")
        print(f"Successfully merged changes from origin/{branch_name} into {branch_name}.")
    except Exception as e:
        print("Merge conflict or other error during merge:", e)
        # Handle conflicts if necessary (resolve them manually or abort the merge)
        local_repo.git.merge("--abort")
        print("Merge aborted due to conflicts.")
    
    ######
    
    ### call inventory systems ###
    
    
    ##############################
    
    #Create the list of dictionary
    result = {'sha': latest_commit.sha, 'date': str(latest_commit.commit.author.date)}
    
    with open("commit_info.json", "w") as f:
        #Write it to file
        json.dump(result, f)
    

# To close connections after use
g.close()