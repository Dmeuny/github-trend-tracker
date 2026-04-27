import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
print("Token loaded:", bool(token))

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "User-Agent": "data-engineering-project"
}

response = requests.get(
    "https://api.github.com/search/repositories",
    headers=headers,
    params={"q": "data engineering", "sort": "stars", "per_page": 5}
)

print("Status:", response.status_code)
print("Items:", len(response.json().get("items", [])))
