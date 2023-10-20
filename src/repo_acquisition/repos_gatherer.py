import os
import time
import pickle
import httpx
import logging
from itertools import product
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_repos(filename: str) -> Dict:
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}


def save_repos(repos: Dict, filename: str):
    with open(filename, "wb") as f:
        pickle.dump(repos, f)


def fetch_repositories(year: int, month: int, day: int, token: str) -> Dict:
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"}
    url = rf"https://api.github.com/search/repositories?q=created:{year}-{str(month).zfill(2)}-{str(day).zfill(2)}+language:jupyter-notebook+stars:%3E50&sort=stars&order=desc&per_page=100"

    with httpx.Client() as client:
        response = client.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch data for {year}-{str(month).zfill(2)}-{str(day).zfill(2)}: {response.text}")
            return {}

        results = response.json().get("items", [])
        return {repo["id"]: {"name": repo["name"], "full_name": repo["full_name"], "html_url": repo["html_url"], "created_at": repo["created_at"], "updated_at": repo["updated_at"], "size": repo["size"], "stargazers_count": repo["stargazers_count"], "topics": repo["topics"], "watchers": repo["watchers"]} for repo in results}


def main():
    years = (2020, 2021, 2022, 2023)
    months = range(1, 13)
    days = range(1, 32)
    filename = "repos_jupyter.pickle"
    token = os.getenv("GITHUB_TOKEN")

    repos = load_repos(filename)

    for year, month, day in product(years, months, days):
        logger.info(f"Year: {year}, month: {month}, day: {day}")

        repos.update(fetch_repositories(year, month, day, token))

        if day % 10 == 0:
            save_repos(repos, filename)
            logger.info(f"Repos gathered so far: {len(repos.keys())}")

        time.sleep(2)

    save_repos(repos, filename)
    logger.info(f"Total repos: {len(repos)}")


if __name__ == "__main__":
    main()
