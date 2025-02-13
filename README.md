# JIRA Issue Generator Agent

This project provides an API service that automatically generates JIRA issues using OpenAI's API and JIRA's REST API. The service is built using FastAPI and provides endpoints for creating and managing JIRA issues programmatically.

## Prerequisites

- Python 3.8 or higher
- JIRA account with API access
- OpenAI API key
- Git (for cloning the repository)

## Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd jira-issue-generator
```

2. Create and activate a virtual environment:

For Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

For Unix/MacOS:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory
2. Add the following environment variables:

```plaintext
OPENAI_API_KEY=your_openai_api_key
URL=your_jira_instance_url
PROJECT_KEY=your_jira_project_key
API_TOKEN=your_jira_api_token
EMAIL=your_jira_email
```

Replace the values with your actual credentials:
- `OPENAI_API_KEY`: Your OpenAI API key
- `URL`: Your JIRA instance URL (e.g., "https://your-domain.atlassian.net")
- `PROJECT_KEY`: The key of your JIRA project where issues will be created
- `API_TOKEN`: Your JIRA API token
- `EMAIL`: Your JIRA account email

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main2:app --reload
```
The server will start on `http://localhost:8000`

2. To test the API endpoints, open a new terminal and run:
```bash
python test.py
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

The `test.py` file contains pre-written test cases for the API endpoints. You can modify these test cases according to your needs.

## Troubleshooting

If you encounter any issues:

1. Ensure all environment variables are correctly set in the `.env` file
2. Verify that your JIRA API token has the necessary permissions
3. Check if the virtual environment is activated before running commands
4. Ensure all dependencies are installed correctly
5. Check the server logs for any error messages

## Contributing

Feel free to submit issues and enhancement requests.

## License

[Specify your license here]
