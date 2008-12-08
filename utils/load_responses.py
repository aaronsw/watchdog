import sys
import mailbox
import email
from datetime import datetime

import web
import config
from utils import helpers, messages

MAILDIR_PATH = config.maildir_path

def getid(msg):
    to = msg.get('To')
    if not to.startswith('p-'): return
    id = email[email.index('p-')+2 : email.index('@')]
    return int(id, 36)
    
def format_date(date):
    """
        >>> date = 'Fri, 22 Aug 2008 11:38:05 +0530 (IST)'
        >>> format_date(date)
        datetime.datetime(2008, 8, 22, 11, 38, 5)
    """
    date = msg.get('Date')
    date = date[0:date.index(' +')] #@@ FIX IT - loosing timezone info
    return datetime.strptime(date, '%a, %d %b %Y %H:%M:%S')
    
def get_msg_body(msg):    
    if msg.is_multipart():
        msgbody = "\n".join(m.get_payload().strip() for m in msg)
    else:
        msgbody = msg.get_payload().strip()
    return msgbody
    
def process(msg):
    #store the msg in db and send followup msg to the sender
    msgid = getid(msg)
    msgbody = get_msg_body(msg)
    received = format_date(msg.get('Date')) #msg.get_date() doesn't work!!
    messages.save_response(msgid, msgbody, received)
    send_followup(msgid, msgbody)

def get_sender_email(msgid):
    uid = messages.get_sender_id(msgid)
    if uid: 
        user = helpers.get_user_by_id(uid)
        if user: return user.email

def send_followup(msgid, response_body):
    from_addr = config.from_address
    to_addr = get_sender_email(msgid)
    if not to_addr: return
    subject = 'FILL IN HERE'
    body = response_body +  'FILL IN HERE'                   
    web.sendmail(from_addr, to_addr, subject, body)
    
if __name__ == '__main__':
    inbox = mailbox.Maildir(MAILDIR_PATH, factory=mailbox.MaildirMessage, create=False)

    for msg in inbox.itervalues():
        process(msg)
