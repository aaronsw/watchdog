import os
import web
from web import form
from settings import db

email_regex = r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{1,4}'
email_list_regex = r'^%s$|^(%s *, *)*(%s)?$' % (email_regex, email_regex, email_regex)
                 
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
      form.Textbox('ptitle', description="Title:", size='80'),         
      form.Textbox('pid', 
            form.notnull,
            form.Validator('ID already exists, Choose a different one.', doesnotexist),
            pre='http://watchdog.net/c/',
            description='URL:',
            size='30'),
      form.Textarea('pdescription', form.notnull, description="Description:", rows='20', cols='80')
      )
      
signform = form.Form(
    form.Textbox('name', form.notnull, description='Name:', post=' *', size='30'),
    form.Textbox('email', 
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:',
            post=' *',
            size='30'),
    form.Dropdown('share_with', 
            [('N', 'Nobody'), 
             ('A', 'Author of this petition'),
             ('E', 'Everybody')
             ],
             description='Share my email with:'),
    form.Textarea('comment',
            description='Comments:',
            cols=70,
            rows=5
            )         
    )

passwordform = form.Form(
    form.Password('password', form.notnull, description="Password:", size='10'),
    form.Password('password_again', form.notnull, description="Repeat:", size='10'),
    validators = [form.Validator("Passwords do not match.", 
                    lambda i: i.password == i.password_again)]
    )

emailform = form.Form(
    form.Textarea('emails', 
                form.notnull, 
                form.regexp(email_list_regex, 'One or more emails are not valid'),
                description="To:", 
                cols=70,
                rows=3),
    form.Textbox('subject', form.notnull, description="Subject:", size='50'),
    form.Textarea('body', form.notnull, description="", cols=70, rows=12)
    )
    
loadcontactsform = form.Form(
    form.Textbox('email', 
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:',
            size='30'),
    form.Radio('provider', 
            ['Google', 'Yahoo'],
            value='Google', 
            description='')
    )
loginform = form.Form(
    form.Textbox('useremail', 
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:'),
    form.Password('password', form.notnull, description='Password:'),
    form.Hidden('redirect')
    )

forgot_password = form.Form(
    form.Textbox('email',
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:'
            )
    )

#@@@ args of writerep function in utils/writerep.py have to be same as names of the inputs below.
writerep = form.Form(
    form.Dropdown('prefix', 
        ['Mr.', 'Mrs.', 'Dr.', 'Ms.', 'Miss'], 
        description='Prefix',
        post='*'
        ),
    form.Textbox('lname',
        form.notnull,
        description='Last Name',
        post='*'
        ),
    form.Textbox('fname',
        form.notnull,
        description='First Name',
        post='*'
        ),    
    form.Textbox('addr1',
        form.notnull,
        description='Address',
        size='20',
        post='*'
        ),
    form.Textbox('addr2',
        description='Address',
        size='20'
        ),    
    form.Textbox('city',
        form.notnull,
        description='City',
        post='*'
        ),
    form.Textbox('zipcode',
        form.notnull,
        form.regexp(r'[0-9]{5}', 'Please enter a valid zip'),
        size='5',
        maxlength='5',
        description='Zip',
        post='*'
        ),
    form.Textbox('phone',
        form.notnull,
        form.regexp(r'[0-9-.]*', 'Please enter a valid phone number'),
        description='Phone',
        post='*'
        ),    
    form.Textbox('email',
        form.notnull,
        form.regexp(email_regex, 'Please enter a valid email'),
        description='Email',
        size='20',
        post='*'
        ),
    form.Textarea('msg',
        form.notnull,
        description='Message',
        rows='15', 
        cols='60',
        post='*'
        )               
    )
    
zip4_textbox = form.Textbox('zip4',
        form.notnull,
        form.regexp(r'[0-9]{4}', 'Please Enter a valid zip'),
        size='4',
        maxlength='4',
        description='Zip4'
    )   

captcha = form.Textbox('captcha',
        form.notnull,
        size='10',
        description='Validation'
)    
