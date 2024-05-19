import os
import openai
from googleapiclient.errors import HttpError
from email_utilities import parse_email, create_mime_message, fetch_messages, create_email_service

# Config variables
SENDER_EMAIL = 'your_email_address@sender.com'
TIME_RANGE = '1h'  # Time range for recent emails (e.g., '1h' for 1 hour)
CUSTOM_INSTRUCTIONS = """My name is Nico. End emails with Best,"""

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def check_needs_reply(email):
    prompt = f"""
    SUBJECT: {email.subject}
    EMAIL CONTENT: {email.content}
    ---
    Task: Above is an email. Your goal is identify if it requires a reply.
    Return YES it it does, otherwise, return NO; (Return ONLY YES or NO)
    """

    chat_completion = client.chat.completions.create(
        model="gpt-4o",
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
    ---
    Additional instructions: {CUSTOM_INSTRUCTIONS}
    """

    chat_completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a virtual assistant trained to draft email replies."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150 
    )

    return chat_completion.choices[0].message.content.strip()

def create_draft_reply(service, inbound_email, reply_content):
    recipient_email = inbound_email.sender # We only reply to the sender of the email
    encoded_message = create_mime_message("Re: " + inbound_email.subject, SENDER_EMAIL, recipient_email, reply_content)
    
    draft_body = {
        'message': {
            'threadId': inbound_email.thread_id,
            'raw': encoded_message
        }
    }

    try:
        draft = service.users().drafts().create(userId='me', body=draft_body).execute()
        print(f"Draft created for thread ID: {inbound_email.thread_id} with draft ID: {draft['id']} and message: {reply_content}")
    except HttpError as error:
        print(f"An error occurred: {error}")

def reply_if_needed(service, email):
    try:
        inbound_email = parse_email(service, email['id'])
        if inbound_email and check_needs_reply(inbound_email):
            reply = generate_reply(inbound_email)
            if reply:
                create_draft_reply(service, inbound_email, reply)
    except Exception as e:
        print(f'An error occurred while processing email: {e}')

def main():
    try:
        service = create_email_service()
        emails = fetch_messages(service, f"in:inbox newer_than:{TIME_RANGE}")
        for email in emails:
            reply_if_needed(service, email)
    except Exception as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    main()