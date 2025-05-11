import os
import requests
from jinja2 import Template
from datetime import datetime, timedelta

USERNAME = "lucifron28"
GH_TOKEN = os.getenv("GH_TOKEN")

if not GH_TOKEN:
    raise ValueError("GH_TOKEN environment variable is not set")

headers = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_contributions():
    today = datetime.utcnow()
    from_calendar = today - timedelta(days=365)
    from_year = datetime(today.year, 1, 1)

    variables = {
        "username": USERNAME,
        "fromYear": from_year.isoformat() + "Z",
        "toYear": today.isoformat() + "Z",
        "fromCalendar": from_calendar.isoformat() + "Z",
        "toCalendar": today.isoformat() + "Z"
    }

    query = """
    query ($username: String!, $fromYear: DateTime!, $toYear: DateTime!, $fromCalendar: DateTime!, $toCalendar: DateTime!) {
      user(login: $username) {
        createdAt
        contributionsThisYear: contributionsCollection(from: $fromYear, to: $toYear) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
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
        headers=headers
    )

    if response.status_code != 200:
        raise Exception(f"GraphQL query failed with status {response.status_code}: {response.text}")

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL query returned errors: {data['errors']}")
    if "data" not in data or "user" not in data["data"]:
        raise Exception(f"Unexpected response format: {data}")

    return data["data"]["user"]

def fetch_contributions_for_period(from_date, to_date):
    variables = {
        "username": USERNAME,
        "from": from_date.isoformat() + "Z",
        "to": to_date.isoformat() + "Z"
    }
    query = """
    query ($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
        }
      }
    }
    """
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    if response.status_code != 200:
        raise Exception(f"GraphQL query failed with status {response.status_code}: {response.text}")
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL query returned errors: {data['errors']}")
    contributions = data["data"]["user"]["contributionsCollection"]
    return sum(contributions[field] for field in [
        "totalCommitContributions",
        "totalIssueContributions",
        "totalPullRequestContributions",
        "totalPullRequestReviewContributions"
    ])

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
    created_at_str = user_data["createdAt"]
    created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
    today = datetime.utcnow()

    total_contributions = 0
    start_date = created_at
    while start_date < today:
        period_end = min(start_date + timedelta(days=365), today)
        period_contributions = fetch_contributions_for_period(start_date, period_end)
        total_contributions += period_contributions
        start_date = period_end

    contributions_this_year_data = user_data["contributionsThisYear"]
    contributions_this_year = sum(contributions_this_year_data[field] for field in [
        "totalCommitContributions",
        "totalIssueContributions",
        "totalPullRequestContributions",
        "totalPullRequestReviewContributions"
    ])

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
