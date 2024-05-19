import os
import mailparser
import base64
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.message import EmailMessage

class Email:
    def __init__(self, thread_id, subject, content, sender):
        self.thread_id = thread_id
        self.subject = subject
        self.content = content
        self.sender = sender

def create_email_service():
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

def fetch_messages(service, query):
    try:
        response = service.users().messages().list(userId='me', q=query).execute()
        messages = response.get('messages', [])
        if not messages:
            print('No messages found.')
            return []
        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return []

def parse_email(service, msg_id):
    response = service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
    email_bytes = base64.urlsafe_b64decode(response['raw'].encode('ASCII'))
    mail = mailparser.parse_from_bytes(email_bytes)

    email = Email(
        thread_id=response.get('threadId'),
        subject=mail.subject,
        content="".join(mail.text_plain),
        sender=mail.from_[0][1]
    )
    return email

def create_mime_message(subject, sender_email, recipient_email, text_content):
    mime_message = EmailMessage()
    mime_message["From"] = sender_email
    mime_message["To"] = recipient_email
    mime_message["Subject"] = subject

    mime_message.set_content(text_content.replace("\n", "<br />\n"), 'html')
    encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

    return encoded_message
