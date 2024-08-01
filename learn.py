from fastapi import APIRouter, HTTPException, Header, status
from typing import Annotated
# from db import upsert_data_to_commits_container
from interfaces import Github_File
from utils import get_changed_files
import requests
import base64
import os
import json
from openai import AzureOpenAI



endpoint = "https://oai-prod-eastus-001.openai.azure.com/"
deployment = "gpt-4o-code-reviewer"


client = AzureOpenAI(
    api_key="7c421dab32794231af5eee7500453042",
    api_version="2024-05-01-preview",
    azure_endpoint=endpoint
)

router = APIRouter(
    prefix='/commit'
)


@router.get('/')
async def new_commit(owner: str, repo: str, branch: str, access_token: Annotated[str, Header()]):
    # Verify access token with owner details from DB
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing.",
            headers={"WWW-Authenticate": "Basic"},
        )
    # Add code here for pushing new commit hash to DB
    return {"message": "commit staged for processing."}


# assuming this will be our github action end point
@router.get('/changed-files')
async def get_changed_files(owner, repo, ref):

    try:
        headers = {
            "Accept": "application/vnd.github+json",
            # Access token to be fetched from db in production
            "Authorization": f"Bearer {'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'}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{ref}"
        response = requests.get(url, headers=headers)
        data = response.json()

        commit_info = {
            'committer_name': data['commit']['author']['name'],
            'commit_message': data['commit']['message'],
            'additions': data['stats']['additions'],
            'deletions': data['stats']['deletions'],
            'sha': data['sha'],
        }

        fetched_files = []

        
        language = 'python' #this variable can be dynamic in future
        ai_responses = []


        system_prompt = f"""
You are a {language} code reviewer. Your task is to identify and report sections of code that need changes, including suggestions, error or exception handling, or optimization. For each identified section, provide both the old code and the new code together in JSON format, encompassing multiple lines if applicable. 

Each file object should include all necessary changes within that file, grouped by the type of change. Follow this pattern:

[
    {{
        "file_name": "main.py",
        "changes": [
            {{
                "type": "type of change whether it is a suggestion, bug_fix or optimization",
                "old_code": "original section of code that needs changes, spanning multiple lines if applicable",
                "new_code": "rewritten section of code, spanning multiple lines if applicable"
            }},
            {{
                "type": "type of change whether it is a suggestion, bug_fix or optimization",
                "old_code": "another section of code that needs changes, spanning multiple lines if applicable",
                "new_code": "rewritten section of code, spanning multiple lines if applicable"
            }}
        ]
    }}
]

Ensure that the response strictly follows this JSON format. Only include sections of code that require changes, and provide them in full blocks for both `old_code` and `new_code`.
Related lines of code should be grouped together for clarity. The response must contain the word 'json' in some form.
"""


        for file in data['files']:
            file_name = file['filename']
            content_url = file['contents_url']
            content_response = requests.get(content_url, headers=headers)
            content_data = content_response.json()
            github_file = Github_File(
                file_name, base64.b64decode(
                    content_data['content']).decode('utf-8'),
                additions=file['additions'],
                deletions=file['deletions'],
                author=data['commit']['author']['name']
            )
            fetched_files.append(github_file)



            review_content = f"Review the following {language} code file:\n\n"
            review_content += f"File: {file_name}\n"
            review_content += f"Content:\n{base64.b64decode(content_data['content']).decode('utf-8')}\n"

            completion = client.chat.completions.create(
                model=deployment,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": review_content
                    }
                ],
                max_tokens=4096,
                response_format={"type": "json_object"},
            )

            response_content = completion.choices[0].message.content
            response_content_cleaned = response_content.replace('$', '')
            response_dict = json.loads(response_content_cleaned)
            ai_responses.append(response_dict)

        return {  
            'commit_info': commit_info,
            'fetched_files': fetched_files,
            'review_content': review_content,
            'ai_responses': ai_responses
        } 



    except Exception as e:
        print('error=>', e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
