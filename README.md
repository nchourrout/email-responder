# Gmail AI Auto Responder
This python script drafts AI responses to incoming emails in Gmail.

*Note: this is the companion code to this [Medium post](https://medium.com/@nchourrout/i-made-an-email-auto-responder-to-conquer-my-writers-block-aa2b91db6741) and is therefore optimized to be easy to understand. Making it production ready will require additional changes. See further down.*

## How it works
1. It opens up a browser window (unless valid credentials are found in `token.pickle`) to sign in with Google
2. It fetches Inbox emails received in the last hour
3. For each email:
    * It extracts Subject, Content (using mailparser) and ThreadId
    * It assesses if the email requires a response (using gpt-4o)
    * If it does, it generates a reply (using gpt-4-turbo)
    * Finally it creates a draft reply to the initial conversation

## Setup
1. Setup Google OAuth for Gmail API with the *modify* scope. Download the `credentials.json` file and add it to the repository ([more details](https://developers.google.com/workspace/guides/create-credentials)).
2. Install necessary libraries.
```bash
pip install -r requirements.txt
```
3. Set up the OPENAI_API_KEY env variable.
```bash
export OPENAI_API_KEY="Your_OpenAI_API_Key"
```
4. Execute the script to sign in to Google and start processing emails.
```bash
python app.py
```
5. To keep this script running hourly, set up a cron job. 
```cron
0 * * * * /usr/bin/python3 /path/to/email-responder/app.py
```

## Caveats
* Relies on a cron job rather than subscriptions.
* Does not consider other emails in the thread.
* Does not learn from past conversations.
* Does not embed text from previous emails in responses.
* Responses may sound too much like ChatGPT.


## Looking for a More Advanced Solution?
If the basic functionalities of this script don't meet all your needs, consider checking out [MailFlowAI.com](https://mailflowai.com). I developed MailFlow to help small businesses efficiently respond to customer emails.

Unlike the basic script, MailFlow offers enhanced capabilities to handle complex email threads, adapt the response tone to match your brand, and learn from diverse data sources like your company website, previous email interactions, and relevant documents.
