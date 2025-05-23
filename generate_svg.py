import os
import sys
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Retrieve GitHub token from environment variable
token = os.getenv("GH_TOKEN")
if not token:
    print("Error: GH_TOKEN environment variable not set.")
    sys.exit(1)

# Retrieve GitHub username from environment variable or command-line argument
username = os.getenv("GH_USERNAME")
if not username:
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        print("Error: GH_USERNAME environment variable not set and no username provided.")
        sys.exit(1)

# Define the GraphQL query to fetch contribution data
query = """
query {
  user(login: "%s") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
""" % username

# Set up API request headers with the token
headers = {
    "Authorization": f"Bearer {token}"
}

# Make the API request
response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)
if response.status_code != 200:
    print(f"Error: API request failed with status {response.status_code}")
    sys.exit(1)

data = response.json()

# Extract contribution days into a list
contribution_days = []
for week in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
    for day in week["contributionDays"]:
        contribution_days.append({
            "date": datetime.strptime(day["date"], "%Y-%m-%d"),
            "count": day["contributionCount"]
        })

# Sort by date (should already be sorted, but ensuring consistency)
contribution_days.sort(key=lambda x: x["date"])

# **Calculate Total Contributions**
total_contributions = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
# Date range for total contributions (typically the last year from the contribution calendar)
total_range_start = contribution_days[0]["date"]
total_range_end = contribution_days[-1]["date"]
total_range = f"{total_range_start.strftime('%b %d, %Y')} - {total_range_end.strftime('%b %d, %Y')}"

# **Calculate Current Streak**
current_streak = 0
current_streak_start = None
current_streak_end = None
for day in reversed(contribution_days):
    if day["count"] > 0:
        if current_streak == 0:
            current_streak_end = day["date"]
        current_streak += 1
        current_streak_start = day["date"]
    elif current_streak > 0:
        break
current_range = (f"{current_streak_start.strftime('%b %d, %Y')} - {current_streak_end.strftime('%b %d, %Y')}"
                 if current_streak > 0 else "None")

# **Calculate Longest Streak**
longest_streak = 0
longest_streak_start = None
longest_streak_end = None
current_count = 0
current_start = None
for day in contribution_days:
    if day["count"] > 0:
        if current_count == 0:
            current_start = day["date"]
        current_count += 1
    else:
        if current_count > longest_streak:
            longest_streak = current_count
            longest_streak_start = current_start
            longest_streak_end = day["date"] - timedelta(days=1)
        current_count = 0
# Check if the final streak is the longest
if current_count > longest_streak:
    longest_streak = current_count
    longest_streak_start = current_start
    longest_streak_end = contribution_days[-1]["date"]
longest_range = (f"{longest_streak_start.strftime('%b %d, %Y')} - {longest_streak_end.strftime('%b %d, %Y')}"
                 if longest_streak > 0 else "None")

# SVG template with placeholders from your provided SVG
svg_template = """
<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'
                style='isolation: isolate' viewBox='0 0 495 195' width='495px' height='195px' direction='ltr'>
        <style>
            @keyframes currstreak {
                0% { font-size: 3px; opacity: 0.2; }
                80% { font-size: 34px; opacity: 1; }
                100% { font-size: 28px; opacity: 1; }
            }
            @keyframes fadein {
                0% { opacity: 0; }
                100% { opacity: 1; }
            }
        </style>
        <defs>
            <clipPath id='outer_rectangle'>
                <rect width='495' height='195' rx='4.5'/>
            </clipPath>
            <mask id='mask_out_ring_behind_fire'>
                <rect width='495' height='195' fill='white'/>
                <ellipse id='mask-ellipse' cx='247.5' cy='32' rx='13' ry='18' fill='black'/>
            </mask>
        </defs>
        <g clip-path='url(#outer_rectangle)'>
            <g style='isolation: isolate'>
                <rect stroke='#111111' fill='#000000' rx='4.5' x='0.5' y='0.5' width='494' height='194'/>
            </g>
            <g style='isolation: isolate'>
                <line x1='165' y1='28' x2='165' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#222222' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
                <line x1='330' y1='28' x2='330' y2='170' vector-effect='non-scaling-stroke' stroke-width='1' stroke='#222222' stroke-linejoin='miter' stroke-linecap='square' stroke-miterlimit='3'/>
            </g>
            <g style='isolation: isolate'>
                <!-- Total Contributions big number -->
                <g transform='translate(82.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#666666' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>
                        2,048
                    </text>
                </g>
                <!-- Total Contributions label -->
                <g transform='translate(82.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#888888' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.7s'>
                        Total Contributions
                    </text>
                </g>
                <!-- Total Contributions range -->
                <g transform='translate(82.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#999999' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.8s'>
                        Aug 10, 2016 - Present
                    </text>
                </g>
            </g>
            <g style='isolation: isolate'>
                <!-- Current Streak label -->
                <g transform='translate(247.5, 108)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#777777' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>
                        Current Streak
                    </text>
                </g>
                <!-- Current Streak range -->
                <g transform='translate(247.5, 145)'>
                    <text x='0' y='21' stroke-width='0' text-anchor='middle' fill='#999999' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 0.9s'>
                        Mar 28, 2019 - Apr 12, 2019
                    </text>
                </g>
                <!-- Ring around number -->
                <g mask='url(#mask_out_ring_behind_fire)'>
                    <circle cx='247.5' cy='71' r='40' fill='none' stroke='#333333' stroke-width='5' style='opacity: 0; animation: fadein 0.5s linear forwards 0.4s'></circle>
                </g>
                <!-- Fire icon -->
                <g transform='translate(247.5, 19.5)' stroke-opacity='0' style='opacity: 0; animation: fadein 0.5s linear forwards 0.6s'>
                    <path d='M -12 -0.5 L 15 -0.5 L 15 23.5 L -12 23.5 L -12 -0.5 Z' fill='none'/>
                    <path d='M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z' fill='#444444' stroke-opacity='0'/>
                </g>
                <!-- Current Streak big number -->
                <g transform='translate(247.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#555555' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='animation: currstreak 0.6s linear forwards'>
                        16
                    </text>
                </g>
            </g>
            <g style='isolation: isolate'>
                <!-- Longest Streak big number -->
                <g transform='translate(412.5, 48)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#666666' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='700' font-size='28px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.2s'>
                        86
                    </text>
                </g>
                <!-- Longest Streak label -->
                <g transform='translate(412.5, 84)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#888888' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='14px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.3s'>
                        Longest Streak
                    </text>
                </g>
                <!-- Longest Streak range -->
                <g transform='translate(412.5, 114)'>
                    <text x='0' y='32' stroke-width='0' text-anchor='middle' fill='#999999' stroke='none' font-family='"Segoe UI", Ubuntu, sans-serif' font-weight='400' font-size='12px' font-style='normal' style='opacity: 0; animation: fadein 0.5s linear forwards 1.4s'>
                        Dec 19, 2016 - Mar 14, 2016
                    </text>
                </g>
            </g>
        </g>
    </svg>
"""

# Define placeholders and their dynamic replacements
placeholders = {
    "2,048": "{:,}".format(total_contributions),  # Total contributions with commas
    "Aug 10, 2016 - Present": total_range,         # Total contributions date range
    "16": str(current_streak),                     # Current streak number
    "Mar 28, 2019 - Apr 12, 2019": current_range,  # Current streak date range
    "86": str(longest_streak),                     # Longest streak number
    "Dec 19, 2016 - Mar 14, 2016": longest_range   # Longest streak date range (corrected in calculation)
}

# Replace placeholders with dynamic data
svg_content = svg_template
for placeholder, value in placeholders.items():
    svg_content = svg_content.replace(placeholder, value)

# Write the updated SVG to file
with open("card.svg", "w") as f:
    f.write(svg_content)

print("Successfully generated card.svg")
