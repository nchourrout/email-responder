import os
import pickle
import base64
import openai
import mailparser
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

class Email:
    def __init__(self, thread_id, subject, content, sender):
        self.thread_id = thread_id
        self.subject = subject
        self.content = content
        self.sender = sender

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
    
def parse_email(service, email_id):
    response = service.users().messages().get(userId='me', id=email_id, format='raw').execute()
    email_bytes = base64.urlsafe_b64decode(response['raw'].encode('ASCII'))
    mail = mailparser.parse_from_bytes(email_bytes)

    email = Email(
        thread_id=response.get('threadId'),
        subject=mail.subject,
        content="".join(mail.text_plain),
        sender=mail.from_[0][1]
    )
    return email

def check_needs_reply(email):
    prompt = f"""
    SUBJECT: {email.subject}
    EMAIL CONTENT: {email.content}
    ---

    Task: Above is an email. Your goal is identify if it requires a reply.
    Return YES it it does, otherwise, return NO; (Return ONLY YES or NO)
    """

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0
    )

    return chat_completion.choices[0].message.content.strip().lower() == "yes"

def generate_reply(email):
    prompt = f"""
    SUBJECT: {email.subject}
    EMAIL CONTENT: {email.content}
    ---

    Task: Compose a reply for the email above
    Ensure that the reply is suitable for a professional email setting and addresses the unknown topic in a clear, structured, and detailed manner.
    ONLY return the text content of the reply.
    """

    chat_completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant trained to draft email replies."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150 
    )

    return chat_completion.choices[0].message.content.strip()

def create_draft_reply(service, inbound_email, reply):
    # Create a MIMEText object to construct the message
    message = MIMEText(reply)
    message['to'] = inbound_email.sender
    message['subject'] = "Re: " + inbound_email.subject

    # Encode the message's bytes for the raw property
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Create the body for the draft
    draft_body = {
        'message': {
            'threadId': inbound_email.thread_id,
            'raw': encoded_message
        }
    }

    try:
        draft = service.users().drafts().create(userId='me', body=draft_body).execute()
        print(f"Draft created for thread ID: {inbound_email.thread_id} with draft ID: {draft['id']} and message: {reply}")
    except HttpError as error:
        print(f"An error occurred: {error}")

def reply_if_needed(service, email):
    inbound_email = parse_email(service, email['id'])
    if check_needs_reply(inbound_email):
        reply = generate_reply(inbound_email)
        create_draft_reply(service, inbound_email, reply)

def main():
    service = create_service()
    emails = get_recent_emails(service)
    for email in emails:
        reply_if_needed(service, email)

if __name__ == '__main__':
    main()