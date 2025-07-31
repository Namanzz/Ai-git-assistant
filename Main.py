# app.py
import os
import json
import google.generativeai as genai
import requests
from github import Github, Auth

# Secrets are loaded by the GitHub Action runner, not a .env file
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# (Copy the three functions: get_pr_diff, post_review_comment, and get_ai_code_review
# from the manual_reviewer.py script above and paste them here)

def get_pr_diff(repo_name: str, pr_number: int) -> str | None:
    # (This function is identical to the one in manual_reviewer.py)
    print(f"Fetching diff for PR #{pr_number} from repo {repo_name}...")
    try:
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        diff_url = pr.diff_url
        headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.diff'}
        response = requests.get(diff_url, headers=headers)
        response.raise_for_status()
        print("Successfully fetched diff.")
        return response.text
    except Exception as e:
        print(f"ERROR: Could not fetch PR diff: {e}")
        return None

def post_review_comment(repo_name: str, pr_number: int, comment_body: str):
    # (This function is identical to the one in manual_reviewer.py)
    print(f"Posting review comment to PR #{pr_number}...")
    try:
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(comment_body)
        print("Successfully posted comment.")
    except Exception as e:
        print(f"ERROR: Could not post comment: {e}")

def get_ai_code_review(code_diff: str) -> str:
    # (This function is identical to the one in manual_reviewer.py,
    # but it takes the API key from the global scope instead of as an argument)
    print("Sending code to Gemini for review...")
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are an expert AI programming assistant acting as a code reviewer on GitHub.
        Provide a concise, constructive code review for the provided code changes (in diff format).
        Format your review in Markdown.
        ---
        {code_diff}
        ---
        """
        response = model.generate_content(prompt)
        print("Review received from AI.")
        return f"### 🤖 AI Code Review\n\n---\n\n{response.text}"
    except Exception as e:
        print(f"ERROR: Could not get AI review: {e}")
        return f"Error: Could not get AI review. Details: {e}"

def main():
    """Main function executed by the GitHub Action."""
    # This is a test comment for our pull request.
    repo_name = os.getenv("GITHUB_REPOSITORY")
    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not all([repo_name, event_path]):
        print("ERROR: Missing required GitHub environment variables.")
        return

    with open(event_path, 'r') as f:
        event_data = json.load(f)

    pr_number = event_data.get("pull_request", {}).get("number")
    if not pr_number:
        print("Could not find PR number in event payload. Exiting.")
        return

    print(f"Processing review for {repo_name}, PR #{pr_number}")

    diff = get_pr_diff(repo_name, pr_number)
    if diff:
        ai_review = get_ai_code_review(diff)
        post_review_comment(repo_name, pr_number, ai_review)

if __name__ == "__main__":
    main()