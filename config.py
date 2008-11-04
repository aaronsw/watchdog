#used to encrypt cookies etc.
try:
    secret_key = file('/home/watchdog/certs/secret_key').read().strip()
except:
    secret_key = 'UuBCsl6nlTEjZASAbqNU' #not to get error while testing on non-server env
#from address in mails sent by watchdog
from_address = '"watchdog.net" <info@watchdog.net>'
maildir_path = '/home/wathdog/Maildir'
send_errors_to = 'bugs@watchdog.net'
test_email = 'test@watchdog.net' #wyr test emails to go to this