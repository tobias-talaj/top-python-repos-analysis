import httpx
import time
import pickle
from itertools import product


years = (2020, 2021, 2022, 2023)
months = range(1, 13)
days = range(1, 32)

try:
    with open('repos_jupyter.pickle', 'rb') as f:
        repos = pickle.load(f)
except FileNotFoundError:
    repos = {}

for year, month, day in product(years, months, days):
    print(f'Year: {year}, month: {month}, day: {day}')
    # if year <= 2020 and month <= 12 and day <= 31:
    #     continue
    
    headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer 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'}
    
    with httpx.Client() as client:
        response = client.get(rf'https://api.github.com/search/repositories?q=created:{year}-{str(month).zfill(2)}-{str(day).zfill(2)}+language:jupyter-notebook+stars:%3E50&sort=stars&order=desc&per_page=100', headers=headers)
        print(response.request.url, response)
        try:
            results = response.json()['items']
                
            for repo in results:
                data = {
                    'name': repo['name'], 
                    'full_name': repo['full_name'],
                    'html_url': repo['html_url'],
                    'created_at': repo['created_at'],
                    'updated_at': repo['updated_at'],
                    'size': repo['size'],
                    'stargazers_count': repo['stargazers_count'],
                    'topics': repo['topics'],
                    'watchers': repo['watchers']
                }
                
                repos[repo['id']] = data
        except Exception as e:
            print(response.text, e)
    if day % 10 == 0:
        with open('repos_jupyter.pickle', 'wb') as f:
            pickle.dump(repos, f)
        print(f'Repos gathered so far: {len(repos.keys())}')
    print('------------------------')

    time.sleep(2)
             
print(f"Total repos: {len(repos)}")