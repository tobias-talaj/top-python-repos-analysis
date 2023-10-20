# top-python-repos-analysis

Save your github token as environment variable:
bash: export GITHUB_TOKEN=your_new_token_here
or
powershell: $env:GITHUB_TOKEN="your_new_token_here"

repos_gatherer gathers repository names for specified timerange and star count and saves it together with other data (size, topics etc) in a pickle file
then
repo_cloner clones those repos and deletes all files (while savind all filenames in a separate file), that arent needed
then
lib_elements_counter counts the components of given libraries used in each python file