"""
Library for managing messages sent to reps and tracking their responses.
"""
import web
from settings import db

def save_msg(frm, to, subj, msg, source_id=None, status=None):
    """saves the given msg and return back msg id. 
    It's assumed that the msg is already sent. 
    msg is always sent from a user to a politician. 
    Optionally the source of the message can be specified  by `source_id`.
    """
    return db.insert('messages', from_id=frm, to_id=to, subject=subj,
		 body=msg, source_id=source_id, sent=status)

def get_msg(msgid):
    """returns the msg with the given `msgid`
    """
    msg = db.select('messages', where='id=$msgid', vars=locals())    
    if msg: return msg[0]

def update_msg_status(msgid, status):
    """updates status of the message with id `msgid` with status.
    """
    db.update('messages', sent=status, where='id=$msgid', vars=locals())

def save_response(msgid, response, timestamp):
    """saves the `response` to msg with `msgid` and returns the response id
    """
    try:
	    return db.insert('responses', msg_id=msgid, response=response, received=timestamp)
    except:
	    pass

def get_responses(msgid):
    """returns all the responses to the msg with the given `msgid`
    """
    return db.select('responses', where='msg_id=$msgid', vars=locals())

def query(frm=None, to=None, source_id=None, limit=None, offset=0, order=None):
    """queries for matching messsages and returns their ids
    """
    where = ''
    if frm: where += 'from_id = $frm and '
    if to:  where += 'to_id = $to and '
    if source_id: where += 'source_id = $source_id and '
    if where:
	    web.rstrips(where, 'and ')
	    where = 'where ' + where
    try:
	    return db.select('messages', where=where, limit=limit, offset=offset, order=order)
    except Exception, details:
	    print where, details

def get_sender_id(msgid):
    """return the id of the sender of the message with id `msgid`.
    """
    u = db.select('messages', what='sender', where='id=$msgid', vars=locals())
    if u: return u[0].sender
