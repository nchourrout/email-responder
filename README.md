# Gmail AI Auto Responder
This python script drafts AI responses to incoming emails. This is the companion code to this [Medium post](https://medium.com/@nchourrout/i-made-an-email-auto-responder-to-conquer-my-writers-block).

*Note: this script that has been optimized to be easy to understand. Making it production ready will require additional changes. See further down.*

## How it works
1. Sign-in with Google (opens up a browser window unless valid credentials are in `token.pickle`)
2. Fetches Inbox emails received in the last hour
3. For each email:
    * Extract Subject, Content (using mailparser), ThreadId
    * Assess if the email requires a response (using gpt-4o)
    * If it does, generate a reply (using gpt-4-turbo)
    * Create a draft reply using Gmail API

## Setup
1. Setup Google OAuth for GMail API with the *modify* scope. Download the `credentials.json` file and add it to the repository ([more details](https://developers.google.com/workspace/guides/create-credentials)).
2. Install necessary libraries.
```bash
pip install -r requirements.txt
```
3. Set up the OPENAI_API_KEY env variable.
```bash
export OPENAI_API_KEY="Your_OpenAI_API_Key
```
4. Execute the script to setup the credentials and start processing emails.
```bash
python app.py
```
5. To keep this script running hourly, set up a cron job. 
```cron
0 * * * * /usr/bin/python3 /path/to/email-responder/app.py
```

## Caveats and alternatives
Caveats:
* Relies on a cron job rather than subscriptions
* Doesn't take into consideration other emails in the thread
* Doesn't learn from past conversations
* The text from previous emails is not embedded in the response
* "Sounds" like ChatGPT

If you're looking for a more robust solution, check-out [MailFlowAI.com](https://mailflowai.com). I made this app to help small businesses draft replies to customer emails. It handles replies to long email threads, adapts its tone to match your company's style, and learns from various data sources such as company website, past email interactions, and PDF documents.