import requests
import json


def test_task_processor(base_url: str = "http://localhost:8000"):
    """Test the task processor API with sample raw text containing multiple items"""

    # Test case with multiple items in different formats
    test_text = """
    Week 1: Project Setup & Core Architecture
     Define tech stack
     Set up repo structure, CI/CD pipelines, environment configs
     Implement authentication (JWT, OAuth, Sign-up/Login, Google Auth)
    """

    print("=== Testing Task Processor ===")
    print(f"Raw Text:\n{test_text}")

    try:
        response = requests.post(
            f"{base_url}/process-tasks/",
            json={"raw_text": test_text},
            timeout=60  # Longer timeout for multiple issues
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            created_issues = response.json()
            print("\nCreated Issues:")
            for issue in created_issues:
                print(f"\nIssue Key: {issue['key']}")
                print(f"Summary: {issue['summary']}")
                print(f"Type: {issue['issue_type']}")
                print(f"Status: {issue['status']}")
        else:
            print("Error Response:")
            print(json.dumps(response.json(), indent=2))

    except Exception as e:
        print(f"Error: {str(e)}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    test_task_processor()