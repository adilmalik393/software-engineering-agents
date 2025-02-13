from pydantic import BaseModel, Field, ValidationError
from enum import Enum
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException
from atlassian import Jira
from openai import OpenAI
import logging
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
app = FastAPI(title="Jira Issue Generator API")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Jira Configuration
JIRA_URL = os.environ.get("URL")
JIRA_PROJECT_KEY = os.environ.get("PROJECT_KEY")
JIRA_API_TOKEN = os.environ.get("API_TOKEN")
JIRA_EMAIL = os.environ.get("EMAIL")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Jira client
try:
    jira_client = Jira(
        url=JIRA_URL,
        username=JIRA_EMAIL,
        password=JIRA_API_TOKEN
    )
    logger.info("Jira client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Jira client: {str(e)}")
    raise

class IssueType(str, Enum):
    BUG = "Bug"
    STORY = "Story"
    TASK = "Task"
    SPIKE = "Spike"

class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class JiraIssue(BaseModel):
    issue_type: IssueType
    summary: str
    description: str
    priority: Priority = Priority.MEDIUM

    class Config:
        extra = "forbid"  # Forbid any extra fields

class RawTextRequest(BaseModel):
    raw_text: str

class CreatedIssue(BaseModel):
    key: str
    summary: str
    issue_type: str
    status: str = "Open"  # Always "Open"

def get_function_definitions():
    """Define the function schema for creating one or more Jira issues."""
    return [
        {
            "name": "create_jira_issues",
            "description": (
                "Create one or more Jira issues. Return a JSON object with a key 'issues' "
                "that is an array of objects. Each object must have the following fields: "
                "issue_type (one of 'Bug', 'Story', 'Task', or 'Spike'), summary, description, "
                "and an optional priority (default is 'Medium')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "issue_type": {
                                    "type": "string",
                                    "enum": ["Bug", "Story", "Task", "Spike"],
                                    "description": "The type of issue to create"
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "A brief summary of the issue"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Detailed description of the issue"
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["High", "Medium", "Low"],
                                    "description": "Priority of the issue"
                                }
                            },
                            "required": ["issue_type", "summary", "description"]
                        }
                    }
                },
                "required": ["issues"]
            }
        }
    ]

async def create_jira_issue(issue: Dict) -> Dict:
    """Create a single Jira issue with the processed information."""
    try:
        issue_data = {
            'project': {'key': JIRA_PROJECT_KEY},
            'summary': issue['summary'],
            'description': issue['description'],
            'issuetype': {'name': issue['issue_type']},
            'priority': {'name': issue.get('priority', 'Medium')},
        }

        logger.info(f"Creating Jira issue with data: {json.dumps(issue_data, indent=2)}")
        response = jira_client.issue_create(fields=issue_data)
        logger.info(f"Jira issue created successfully: {json.dumps(response, indent=2)}")

        return response

    except Exception as e:
        logger.error(f"Error creating Jira issue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating Jira issue: {str(e)}"
        )

async def process_tasks_with_llm(raw_text: str) -> List[CreatedIssue]:
    """Process raw text using LLM to extract one or more Jira issues."""
    try:
        with open("context.txt", "r", encoding="utf-8") as f:
            context = f.read()

        system_prompt = ("You are a helpful assistant that analyzes text and creates structured Jira issues."
                         "now which priority belongs to which issue and what will be the template you see this "
                         f"context for your reference. {context}"
                        )
        prompt = f"""
Analyze the following text containing tasks or items.
For each bullet point or distinct item, do the following:
1. Identify the issue type by choosing one from Bug, Story, Task, or Spike.
2. Create a clear, concise summary.
3. Format a detailed description following the appropriate template based on the identified issue type.
Return a JSON object with a key "issues" that is an array of objects. Each object must contain:
   - issue_type (must be one of 'Bug', 'Story', 'Task', or 'Spike'),
   - summary,
   - description,
   - priority (optional, default is 'Medium').
IMPORTANT: If only one task is provided, the "issues" array should contain exactly one object.
Raw Text:
{raw_text}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Make a single call to get all issues at once.
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            functions=get_function_definitions(),
            function_call={"name": "create_jira_issues", "auto": True}
        )

        message = completion.choices[0].message

        if not message.function_call:
            raise HTTPException(
                status_code=400,
                detail="LLM did not return a function call."
            )

        try:
            function_args = json.loads(message.function_call.arguments)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise HTTPException(
                status_code=400,
                detail="Failed to decode JSON from function call arguments."
            )

        issues_data = function_args.get("issues")
        if not issues_data or not isinstance(issues_data, list):
            raise HTTPException(
                status_code=400,
                detail="LLM output did not include a valid 'issues' array."
            )

        created_issues = []
        for issue_obj in issues_data:
            # Fallback: If 'issue_type' is missing or empty, default to "Task".
            if "issue_type" not in issue_obj or not issue_obj["issue_type"]:
                logger.warning("LLM output missing 'issue_type', defaulting to 'Task'")
                issue_obj["issue_type"] = "Task"
            # Validate using Pydantic
            try:
                jira_issue_data = JiraIssue(**issue_obj)
            except Exception as e:
                logger.error(f"Validation error: {e}")
                raise HTTPException(
                    status_code=400,
                    detail="One of the issues from LLM output did not match the expected schema."
                )
            # Create the Jira issue.
            response = await create_jira_issue(jira_issue_data.dict())
            created_issue = CreatedIssue(
                key=response['key'],
                summary=jira_issue_data.summary,
                issue_type=jira_issue_data.issue_type.value,
                status="Open"
            )
            created_issues.append(created_issue)

        return created_issues

    except Exception as e:
        logger.error(f"Error processing tasks with LLM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing tasks: {str(e)}"
        )

@app.post("/process-tasks/", response_model=List[CreatedIssue])
async def process_tasks(request: RawTextRequest):
    """Process raw text and create Jira issues accordingly."""
    try:
        created_issues = await process_tasks_with_llm(request.raw_text)
        return created_issues

    except Exception as e:
        logger.error(f"Error in process_tasks endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="debug")
