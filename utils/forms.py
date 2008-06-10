import os
import web
from web import form

db = web.database(dbn=os.environ.get('DATABASE_ENGINE', 'postgres'),
                  db='watchdog_dev')
email_regex = r'[\w\.]+@[\w\.]+\.[a-zA-Z]{1,4}'
                 
def doesnotexist(pid):
    "Return True if petition with id `pid` does not exist"
    return not(bool(db.select('petition', where='id=$pid', vars=locals())))
                
petitionform = form.Form(
      form.Textbox('id', 
            form.notnull,
            form.Validator('ID already exists, Choose a different one.', doesnotexist),
            post='(this becomes a part of your petition URL)',
            description='Petition ID:',
            size='30'),
      form.Textbox('title', description="Title:", size='80'),         
      form.Textarea('description', description="Description:", rows='20', cols='80'),        
      form.Textbox('email', 
            form.notnull, 
            form.regexp(email_regex, 'Please enter a valid email'),
            description="Your email:",
            size='30')
      )
      
signform = form.Form(
    form.Textbox('name', description='Name', size='30'),
    form.Textbox('email', 
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email',
            size='30')
    )
