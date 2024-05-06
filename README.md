# Email Responder
This is an example python application that automatically draft responses to incoming emails. This is the companion code to this [post on Medium](#), which goes into more details about the system and its drawbacks.

*Note: this simplified script that has been optimized to be easy to understand. Making it production ready will require additional changes.*

## How it works
1. Sign-in with Google (opens up a browser window unless valid credentials are in `token.pickle`)
2. Fetches Inbox emails received in the last hour
3. For each email:
    1. Extract Subject, Content (using mailparser), ThreadId
    2. Assess if the email requires a response (using gpt-3.5-turbo)
    3. If it does, generate a reply (using gpt-4-turbo)
    4. Create a draft reply using Gmail API

## Setup and Installation
1. Add Google OAuth for GMail API with the modify scope, then download and add `credentials.json` to the repository. [More details here](https://developers.google.com/workspace/guides/create-credentials)
2. (Optional) Set up a cron job: Since the script is designed to check emails received within the past hour, it should be scheduled to run hourly. You can achieve this by setting up a cron job.
```cron
0 * * * * /usr/bin/python3 /path/to/email-responder/script.py
```