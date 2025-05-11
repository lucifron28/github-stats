import os
import requests
from jinja2 import Template
from datetime import datetime, timedelta

USERNAME = "lucifron28"
GH_TOKEN = os.getenv("GH_TOKEN")

headers = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def fetch_contributions():
    today = datetime.utcnow()
    from_calendar = today - timedelta(days=365)
    from_year = datetime(today.year, 1, 1)
    from_total = datetime(2000, 1, 1)

    variables = {
        "username": USERNAME,
        "fromTotal": from_total.isoformat() + "Z",
        "toTotal": today.isoformat() + "Z",
        "fromYear": from_year.isoformat() + "Z",
        "toYear": today.isoformat() + "Z",
        "fromCalendar": from_calendar.isoformat() + "Z",
        "toCalendar": today.isoformat() + "Z"
    }

    query = """
    query ($username: String!, $fromTotal: DateTime!, $toTotal: DateTime!, $fromYear: DateTime!, $toYear: DateTime!, $fromCalendar: DateTime!, $toCalendar: DateTime!) {
      user(login: $username) {
        totalContributions: contributionsCollection(from: $fromTotal, to: $toTotal) {
          totalContributions
        }
        contributionsThisYear: contributionsCollection(from: $fromYear, to: $toYear) {
          totalContributions
        }
        contributionsCollection(from: $fromCalendar, to: $toCalendar) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers={"Authorization": f"Bearer {GH_TOKEN}"}
    )
    if response.status_code != 200:
        raise Exception(f"GraphQL query failed: {response.text}")
    data = response.json()
    return data["data"]["user"]

def fetch_total_stars():
    url = f"https://api.github.com/users/{USERNAME}/repos"
    total_stars = 0
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repositories: {response.status_code} - {response.text}")
        repos = response.json()
        for repo in repos:
            total_stars += repo["stargazers_count"]
        url = response.links.get('next', {}).get('url')
    return total_stars

def fetch_workflow_runs():
    url = f"https://api.github.com/users/{USERNAME}/repos"
    total_runs = 0
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repositories: {response.status_code} - {response.text}")
        repos = response.json()
        for repo in repos:
            runs_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/actions/runs"
            runs_response = requests.get(runs_url, headers=headers)
            if runs_response.status_code == 200:
                runs_data = runs_response.json()
                total_runs += runs_data.get("total_count", 0)
        url = response.links.get('next', {}).get('url')
    return total_runs

def calculate_streaks(contribution_days):
    if not contribution_days:
        return 0, 0

    max_streak = 0
    temp_streak = 0
    prev_date = None
    for day in contribution_days:
        date = datetime.strptime(day["date"], "%Y-%m-%d").date()
        count = day["contributionCount"]
        if prev_date is not None and (date - prev_date).days != 1:
            temp_streak = 0
        if count > 0:
            temp_streak += 1
            max_streak = max(max_streak, temp_streak)
        else:
            temp_streak = 0
        prev_date = date

    current_streak = 0
    for day in reversed(contribution_days):
        count = day["contributionCount"]
        if count > 0:
            current_streak += 1
        else:
            break

    return current_streak, max_streak

def get_github_data():
    user_data = fetch_contributions()
    
    total_contributions = user_data["totalContributions"]["totalContributions"]
    contributions_this_year = user_data["contributionsThisYear"]["totalContributions"]
    weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
    contribution_days = [day for week in weeks for day in week["contributionDays"]]
    
    current_streak, longest_streak = calculate_streaks(contribution_days)
    total_stars = fetch_total_stars()
    total_workflow_runs = fetch_workflow_runs()
    
    return {
        "total_contributions": total_contributions,
        "contributions_this_year": contributions_this_year,
        "total_stars": total_stars,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_workflow_runs": total_workflow_runs
    }

def render_svg(stats):
    with open("template.svg") as file:
        template = Template(file.read())
    return template.render(stats)

def main():
    stats = get_github_data()
    svg_content = render_svg(stats)
    with open("github-stats.svg", "w") as f:
        f.write(svg_content)

if __name__ == "__main__":
    main()
