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


def get_categorized_prs(prs):
    """
    Passes in the PR titles and urls to chatGPT for categorization
    """
    print("Getting categorized PRs")

    system = {
    'role':
    'system',
    'content':
    f'''
    You are a Product Manager for the Bitcoin Dev Kit. 
    You are preparing a weekly dev call by organizing the open Pull Requests into useful categories.
    Output the categories and the PRs that belong to each category in the required output structure.
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
        model='gpt-3.5-turbo',
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

def generate_notes(repo_url):
    # parse out repo owner and repo name from repo url
    repo_owner = repo_url.split("/")[-2]
    repo_name = repo_url.split("/")[-1]
    prs = get_prs(repo_owner, repo_name)
    print("Got PRs")
    categorized_prs = get_categorized_prs(prs)
    print("Got Categorized PRs")

    # build the markdown formatted string
    md_string = ""
    for category, prs in categorized_prs.items():
        md_string += f"## {category}\n"
        for pr in prs:
            md_string += f"- {pr}\n\n"
    md = markdown(md_string)
    print("Generated markdown")
    print(md_string)
    return md


