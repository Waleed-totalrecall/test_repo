
from fastapi import APIRouter, HTTPException, Header, status
from typing import Annotated
from interfaces import Github_File
import requests
import base64
import json
from openai import AzureOpenAI

# Endpoint and deployment configuration
endpoint = "https://oai-prod-eastus-001.openai.azure.com/"
deployment = "gpt-4o-code-reviewer"

client = AzureOpenAI(
    api_key=API_KEY,
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
async def get_changed_files(owner: str, repo: str, ref: str):
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {'Access_Token'}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{ref}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
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
            content_response.raise_for_status()
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
                "content": """You are a Python code reviewer. Please review the following code based on the following criteria:
                1. Basic Clarity and Structure: Assess whether the code is clear, easy to read, and logically organized. Suggest improvements to enhance its understandability and maintainability.
                2. Commenting and Documentation: Identify areas where comments or documentation are necessary to improve understanding.
                3. Refactoring Suggestions: Highlight opportunities for refactoring to improve readability and code structure. Recommend specific changes to make the code cleaner and more maintainable.
                4. Naming Conventions: Evaluate the naming conventions used for variables and functions. Suggest improvements to enhance clarity and understanding.
                5. Code Simplification: Recommend ways to simplify complex code segments to make them more readable and easier to understand.

                Provide detailed suggestions and explanations for each of the above criteria, including specific line numbers where changes are needed. You must return the response strictly in JSON format.
                """
            },
            {
                "role": "system",
                "content": """You are a Python code reviewer. Please review the following code based on the following criteria:
                1. Basic Error Handling: Ensure that the code gracefully handles common errors and exceptions. Suggest improvements where error handling is missing or insufficient.
                2. Detailed Exception Messages: Check if the exception messages provide sufficient details for debugging and suggest enhancements where needed.
                3. Try-Except Blocks: Evaluate the use of try-except blocks and recommend best practices for their usage, including avoiding broad exception catches.
                4. Resource Management: Verify that resources such as files or network connections are properly managed and closed in case of errors.
                5. Edge Cases and Unexpected Inputs: Identify potential edge cases and unexpected inputs that could cause the code to fail. Suggest additional error handling to make the code more robust.

                Provide detailed suggestions and explanations for each of the above criteria, including specific line numbers where changes are needed. You must return the response strictly in JSON format.
                """
            },
            {
                "role": "system",
                "content": """You are a Python code reviewer. Please review the following code based on the following criteria:
                1. Performance Bottlenecks: Identify any performance bottlenecks in the code and suggest optimizations to improve execution speed.
                2. Algorithm Efficiency: Assess the efficiency of the algorithms used and recommend more efficient alternatives where applicable.
                3. Resource Management: Ensure that resources such as memory and CPU are used efficiently. Suggest improvements to reduce resource consumption.
                4. Concurrency and Parallelism: Evaluate opportunities for using concurrency or parallelism to enhance performance. Suggest specific techniques or libraries that could be used.
                5. Code Profiling: Recommend profiling tools and techniques that could help in identifying performance issues and optimizing the code further.

                Provide detailed suggestions and explanations for each of the above criteria, including specific line numbers where changes are needed. You must return the response strictly in JSON format.
                """
            }
        ]

        # Dictionary to hold the suggestions for JSON output
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
            )
            
            # Extract response content and parse JSON if necessary
            content = completion.choices[0].message.content
            try:
                response_json = json.loads(content)
            except json.JSONDecodeError:
                response_json = {"error": "Response is not in valid JSON format"}

            suggestion_contents[f"review_{i+1}"] = response_json

        return {
            'commit_info': commit_info,
            'fetched_files': [f.dict() for f in fetched_files],
            'review_content': review_content,
            'suggestion_contents': suggestion_contents
        }

    except Exception as e:
        print('error=>', e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
