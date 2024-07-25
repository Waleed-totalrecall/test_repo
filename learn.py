
from fastapi import APIRouter, HTTPException, Header, status
from typing import Annotated, List
from interfaces import Github_File
import requests
import base64
import json
from pydantic import BaseModel
from openai import AzureOpenAI

# endpoint and deployment
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
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"message": "commit staged for processing."}

@router.get('/changed-files')
async def get_changed_files(owner, repo, ref):
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {'Github_api'}",
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
        language = 'python'
        review_content = f"Review the following {language} code files:\n\n"

        for file in data['files']:
            file_name = file['filename']
            content_url = file['contents_url']
            content_response = requests.get(content_url, headers=headers)
            content_data = content_response.json()
            github_file = Github_File(
                file_name, base64.b64decode(content_data['content']).decode('utf-8'),
                additions=file['additions'],
                deletions=file['deletions'],
                author=data['commit']['author']['name']
            )
            fetched_files.append(github_file)
            review_content += f"File: {file_name}\n"
            review_content += f"Content:\n{base64.b64decode(content_data['content']).decode('utf-8')}\n"

        # Define prompts
        prompts = [
            {
                "role": "system",
                "content": """You are a Python code reviewer. Please review the following code based on the criteria listed below and only reply with JSON in the format specified. For each file, provide a clear improvement by rewriting the code to enhance readability, clarity, and structure:
                1. Basic Clarity and Structure: Assess whether the code is clear, easy to read, and logically organized.
                2. Commenting and Documentation: Identify areas where comments or documentation are necessary.
                3. Refactoring Suggestions: Highlight opportunities for refactoring to improve readability and code structure.
                4. Naming Conventions: Evaluate the naming conventions used for variables and functions.
                5. Code Simplification: Recommend ways to simplify complex code segments.
                Provide suggestions in the following JSON format:
                [
                    {
                        "file_name": "filename.py",
                        "old_code": "old code given to you as an input",
                        "new_code": "code rewritten by you"
                    }
                ]
"""
            },
            {
                "role": "system",
                "content": """You are a Python code reviewer. Please review the following code based on the criteria listed below and only reply with JSON in the format specified. For each file, provide improvements to error and exception handling:
                1. Basic Error Handling: Ensure the code gracefully handles common errors and exceptions.
                2. Detailed Exception Messages: Check if the exception messages provide sufficient details for debugging.
                3. Try-Except Blocks: Evaluate the use of try-except blocks and recommend best practices.
                4. Resource Management: Verify that resources are properly managed and closed in case of errors.
                5. Edge Cases and Unexpected Inputs: Identify potential edge cases and unexpected inputs.
                Provide suggestions in the following JSON format:
                [
                    {
                        "file_name": "filename.py",
                        "old_code": "old code given to you as an input",
                        "new_code": "code rewritten by you"
                    }
                ]
                """
            },
            {
                "role": "system",
                "content": """You are a Python code reviewer. Please review the following code based on the criteria listed below and only reply with JSON in the format specified. For each file, suggest optimizations to improve performance:
                1. Performance Bottlenecks: Identify any performance bottlenecks and suggest optimizations.
                2. Algorithm Efficiency: Assess the efficiency of the algorithms used and recommend more efficient alternatives.
                3. Resource Management: Ensure resources such as memory and CPU are used efficiently.
                4. Concurrency and Parallelism: Evaluate opportunities for using concurrency or parallelism.
                5. Code Profiling: Recommend profiling tools and techniques for identifying performance issues.
                Provide suggestions in the following JSON format:
                [
                    {
                        "file_name": "filename.py",
                        "old_code": "old code given to you as an input",
                        "new_code": "code rewritten by you"
                    }
                ]
                """
            }
        ]

        # Dictionary to hold the suggestions for response
        suggestion_contents = {}

        for i, prompt in enumerate(prompts):
            completion = client.chat.completions.create(
                model=deployment,
                messages=[
                    prompt,
                    {
                        "role": "user",
                        "content": review_content
                    },
                ],
                response_format={"type": "json_object"}
            )
            suggestion_content = completion.choices[0].message.content

            # Use case specific names
            use_case_names = [
                "Readability, Clarity, and Code Structure",
                "Error and Exception Handling",
                "Optimization Suggestions"
            ]

            suggestion_contents[use_case_names[i]] = suggestion_content

        result = {
            'commit_info': commit_info,
            'fetched_files': fetched_files,
            'review_content': review_content,
            'suggestion_contents': suggestion_contents
        }
            
        print (result)
        return result
    except Exception as e:
        print('error=>', e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
