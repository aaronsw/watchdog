import os
import web
from web import form
from . settings import db

email_regex = r'[\w\.]+@[\w\.]+\.[a-zA-Z]{1,4}'
                 
def doesnotexist(pid):
    "Return True if petition with id `pid` does not exist"
    return not(bool(db.select('petition', where='id=$pid', vars=locals())))
                
petitionform = form.Form(
      form.Textbox('title', description="Title:", size='80'),         
      form.Textbox('id', 
            form.notnull,
            form.Validator('ID already exists, Choose a different one.', doesnotexist),
            post='(this becomes a part of your petition URL)',
            description='Petition ID:',
            size='30'),
      form.Textarea('description', description="Description:", rows='20', cols='80'),        
      form.Textbox('email', 
            form.notnull, 
            form.regexp(email_regex, 'Please enter a valid email'),
            description="Your email:",
            size='30')
      )
      
signform = form.Form(
    form.Textbox('name', form.notnull, description='Name:', size='30'),
    form.Textbox('email', 
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:',
            size='30')    
    )

passwordform = form.Form(
    form.Password('password', form.notnull, description="Password:", size='30'),
    form.Password('password_again', form.notnull, description="Repeat password :", size='30'),
    validators = [form.Validator("Passwords do not match.", lambda i: i.password == i.password_again)]
    )