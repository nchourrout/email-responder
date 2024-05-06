import os
import pickle
import base64
import openai
import mailparser
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def create_service():
    creds = None
    # Load existing creds from the file if it exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing access token: {e}")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes=['https://www.googleapis.com/auth/gmail.modify']
            )
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def get_recent_emails(service):
    time_range = '1h'
    
    # Construct query to search for emails within the time range and in the inbox
    query = f"in:inbox newer_than:{time_range}"

    try:
        # Execute query to fetch recent emails
        response = service.users().messages().list(userId='me', q=query).execute()
        messages = response.get('messages', [])
        if not messages:
            print('No new messages.')
            return []
        return messages
            
    except Exception as error:
        print(f'An error occurred: {error}')
        return []
    
def parse_email(service, email):
    response = service.users().messages().get(userId='me', id=email['id'], format='raw').execute()
    thread_id = response.get('threadId')

    # Decode the email content from raw format to avoid dealing with individual MIME parts
    email_bytes = base64.urlsafe_b64decode(response['raw'].encode('ASCII'))
    mail = mailparser.parse_from_bytes(email_bytes)

    # Extract subject and text content from the email
    subject = mail.subject
    text_content = "".join(mail.text_plain)

    return {
        'threadId': thread_id,
        'subject': subject,
        'content': text_content
    }

def check_needs_reply(subject, content):
    prompt = f"""
    SUBJECT: {subject}
    EMAIL CONTENT: {content}
    ---

    Above is an email. Your goal is identify if it requires a reply.
    Return YES it it does, otherwise, return NO; (Return ONLY YES or NO)

    ANSWER: 
    """

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0
    )

    # Extract the text from the completion choice and strip whitespace
    response = chat_completion.choices[0].message.content.strip().lower() == "yes"
    print(response)
    return response

def gen_reply(subject, content):
    prompt = f"""
    SUBJECT: {subject}
    EMAIL CONTENT: {content}
    ---

    Above is an email. Your goal is to generate a reply. ONLY the reply is needed.

    ANSWER:
    """
    
    chat_completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant trained to draft email replies."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150 
    )

    # Extract the text from the completion choice and strip whitespace
    reply = chat_completion.choices[0].message.content.strip()
    print(reply)
    return reply

def create_draft_reply(service, thread_id, reply):
    message = {
        'message': {
            'threadId': thread_id,
            'raw': base64.urlsafe_b64encode(reply.encode()).decode()
        }
    }

    try:
        service.users().drafts().create(userId='me', body=message).execute()
        print(f"Draft created for thread ID: {thread_id}")
    except HttpError as error:
        print(f"An error occurred: {error}")

def reply_if_needed(service, email):
    parsed_email = parse_email(service, email)
    subject = parsed_email['subject']
    content = parsed_email['content']
    thread_id = parsed_email['threadId']
    needs_reply = check_needs_reply(subject, content)
    if needs_reply:
        reply = gen_reply(subject, content)
        create_draft_reply(service, thread_id, reply)

def main():
    service = create_service()
    emails = get_recent_emails(service)
    for email in emails:
        reply_if_needed(service, email)

if __name__ == '__main__':
    main()