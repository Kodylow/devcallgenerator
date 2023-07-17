from github import Github
from dotenv import load_dotenv
import os
import datetime
import openai
load_dotenv()
import markdown

openai.api_key = os.environ['OPENAI_API_KEY']

import requests
from dateutil.parser import parse
from operator import itemgetter
import json

system = {
    'role':
    'system',
    'content':
    f'''
    You are a Product Manager for a Bitcoin Open Source Project. 
    You are preparing a weekly dev call by organizing the open Pull Requests and Issues into useful categories.
    Output the categories and the PRs/Issues that belong to each category in the required output structure. Categories we normally use include (but not limited to): Consensus, On-Chain, Lightning Gateway, Devimint/Testing, and Misc, but make others too.
    Required Output Structure:
    {{
        "Category1": [
            123,
        ],
        "Category2": [
            456,
            789
        ]
    }}
    '''
    }

def get_categorized_prs(prs):
    """
    Passes in the PR titles and urls to chatGPT for categorization
    """
    print("Getting categorized PRs")

    pr_index = {}
    # Create a dictionary of PR number to PR message
    for pr in prs:
        pr_index[str(pr['number'])] = f"#{pr['number']} - [{pr['title']}]({pr['url']})"
    pr_messages = "\n".join(pr_index.values())
    user = {
    'role':
    'user',
    'content': pr_messages
    }

    print("Sending messages to chatGPT")
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[system, user],
    )
    res = response.choices[0].message.content
    print("Got response from chatGPT: ", res)
    combined = {}
    for k, v in json.loads(res).items():
        temp = []
        for i in v:
            try:
                temp.append(pr_index[str(i)])
            except KeyError:
                pass
        combined[k] = temp
    return combined

def get_prs(repo_owner, repo_name):
    print("Getting PRs")
    headers = {"Authorization": "Bearer " + os.environ['GITHUB_TOKEN']}

    # Query last 100 PRs 
    query = """
    {{
      repository(name: "{repo_name}", owner: "{repo_owner}") {{
        pullRequests(last: 100, states: OPEN) {{
          nodes {{
            title
            number
            updatedAt
            createdAt
            url
            comments {{
              totalCount
            }}
            reviews {{
              totalCount
            }}
            body
          }}
        }}
      }}
    }}
    """.format(repo_name=repo_name, repo_owner=repo_owner)

    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        result = request.json()
        prs = result['data']['repository']['pullRequests']['nodes']
        
        # Filter PRs updated in the last 7 days
        prs = [pr for pr in prs if (parse(pr['updatedAt']).date() - datetime.date.today()).days <= 7]

        # Sort PRs by combined comment and review count
        prs.sort(key=lambda pr: pr['comments']['totalCount'] + pr['reviews']['totalCount'], reverse=True)
        
        return prs
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

repo_owner = "fedimint"
repo_name = "fedimint"

from markdown import markdown

def get_issues(repo_owner, repo_name):
    print("Getting Issues")
    headers = {"Authorization": "Bearer " + os.environ['GITHUB_TOKEN']}

    # Query last 100 issues
    query = """
    {{
      repository(name: "{repo_name}", owner: "{repo_owner}") {{
        issues(last: 100, states: OPEN) {{
          nodes {{
            title
            number
            updatedAt
            createdAt
            url
            comments {{
              totalCount
            }}
            body
          }}
        }}
      }}
    }}
    """.format(repo_name=repo_name, repo_owner=repo_owner)

    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        result = request.json()
        issues = result['data']['repository']['issues']['nodes']

        # Filter issues updated in the last 7 days
        issues = [issue for issue in issues if (parse(issue['updatedAt']).date() - datetime.date.today()).days <= 7]

        # Sort issues by comment count
        issues.sort(key=lambda issue: issue['comments']['totalCount'], reverse=True)

        return issues
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def get_categorized_issues(issues):
    """
    Passes in the issue titles and urls to chatGPT for categorization
    """
    print("Getting categorized issues")

    issue_index = {}
    # Create a dictionary of issue number to issue message
    for issue in issues:
        issue_index[str(issue['number'])] = f"#{issue['number']} - [{issue['title']}]({issue['url']})"
    issue_messages = "\n".join(issue_index.values())
    user = {
        'role':
        'user',
        'content': issue_messages
    }

    print("Sending messages to chatGPT")
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[system, user],
    )
    res = response.choices[0].message.content
    print("Got response from chatGPT: ", res)
    combined = {}
    for k, v in json.loads(res).items():
        temp = []
        for i in v:
            try:
                temp.append(issue_index[str(i)])
            except KeyError:
                pass
        combined[k] = temp
    return combined


def generate_notes(repo_url):
    # parse out repo owner and repo name from repo url
    repo_owner = repo_url.split("/")[-2]
    repo_name = repo_url.split("/")[-1]
    prs = get_prs(repo_owner, repo_name)
    print("Got PRs")
    categorized_prs = get_categorized_prs(prs)
    print("Got Categorized PRs")

    issues = get_issues(repo_owner, repo_name)
    print("Got Issues")
    categorized_issues = get_categorized_issues(issues)
    print("Got Categorized Issues")

    # build the markdown formatted string
    md_string = "# Weekly Dev Call:\n\n"

    md_string += "## PRs:\n"
    for category, prs in categorized_prs.items():
        md_string += f"### {category}\n"
        for pr in prs:
            md_string += f"- {pr}\n"
        md_string += "\n"

    md_string += "## Issues:\n"
    for category, issues in categorized_issues.items():
        md_string += f"### {category}\n"
        for issue in issues:
            md_string += f"- {issue}\n"
        md_string += "\n"

    md = markdown(md_string)
    print("Generated markdown")
    print(md_string)
    return md_string

# call generate_notes with the repo url and save the output markdown to a file
repo_url = "https://github.com/fedimint/fedimint"
md = generate_notes(repo_url)
with open("notes.md", "w") as f:
    f.write(md)

