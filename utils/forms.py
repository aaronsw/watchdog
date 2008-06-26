import os
import web
from web import form
from . settings import db

email_regex = r'[\w\.]+@[\w\.]+\.[a-zA-Z]{1,4}'
                 
def doesnotexist(pid):
    "Return True if petition with id `pid` does not exist"
    exists = bool(db.select('petition', where='id=$pid', vars=locals()))
    return pid != 'new' and not(exists)
                
petitionform = form.Form(
      form.Textbox('email', 
            form.notnull, 
            form.regexp(email_regex, 'Please enter a valid email'),
            description="Your email:",
            size='30'),
      form.Textbox('title', description="Title:", size='80'),         
      form.Textbox('id', 
            form.notnull,
            form.Validator('ID already exists, Choose a different one.', doesnotexist),
            pre='http://watchdog.net/c/',
            description='URL:',
            size='30'),
      form.Textarea('description', form.notnull, description="Description:", rows='20', cols='80')
      )
      
signform = form.Form(
    form.Textbox('name', form.notnull, description='Name:', post=' *', size='30'),
    form.Textbox('email', 
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:',
            post=' *',
            size='30'),
    form.Dropdown('email_privacy', 
            [('N', 'Nobody'), 
             ('A', 'Author of this petition'),
             ('E', 'Everybody')
             ],
             description='Share my email with:'),
    form.Textarea('comment',
            description='Comments:',
            cols=70,
            rows=10
            )         
    )

passwordform = form.Form(
    form.Password('password', form.notnull, description="Password:", size='10'),
    form.Password('password_again', form.notnull, description="Repeat:", size='10'),
    validators = [form.Validator("Passwords do not match.", lambda i: i.password == i.password_again)]
    )
