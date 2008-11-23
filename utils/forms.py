import web
from web import form
from settings import db
from wyrutils import getdists
from auth import loginuser

email_regex = r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{1,4}'
email_list_regex = r'^%s$|^(%s *, *)*(%s)?$' % (email_regex, email_regex, email_regex)

def petitionnotexists(pid):
    "Return True if petition with id `pid` does not exist"
    exists = bool(db.select('petition', where='id=$pid', vars=locals()))
    return pid != 'new' and not(exists)

def getstates():
    return [(s.code, s.name) for s in db.select('state', what='code, name', order='name')]

class ZipValidator:
    def valid(self, i):
        dists = getdists(i.zipcode, i.zip4, i.addr1+i.addr2)
        msg = ''
        if len(dists) > 1 and not i.zip4:
            msg = "Zipcode is shared between two districts. Enter zip4 too."
        elif len(dists) != 1:
            msg = "Couldn't find district for this address and zip"
        elif not dists[0].startswith(i.state):
            msg = "Zipcode and address doesn't fall in the selected state"
        web.ctx.zip_validator_msg = msg
        return False if msg else True
    
    def get_msg(self):
        return web.ctx.get('zip_validator_msg', '')
    msg = property(get_msg)

def emailnotexists(email):
    "Return True if account with email `email` does not exist"
    exists = bool(db.select('users', where='email=$email', vars=locals()))
    return not(exists)
    
def check_len(phone):
    return len(web.numify(phone)) <= 15

petitionform = form.Form(
      form.Textbox('ptitle', form.Validator("Title can't be blank", bool), description="Title:", size='80'),
      form.Textbox('pid', form.Validator("Address can't be blank", bool), form.Validator('ID already exists, Choose a different one.', petitionnotexists),
                    pre='http://watchdog.net/c/', description='URL:', size='30'),
      form.Textarea('msg', form.Validator("Description can't be blank", bool), description="Description:", rows='15', cols='80'),
      form.Checkbox('tocongress', value='', description="Petition to Congress?"),
      form.Hidden('userid')
      )

wyrform = form.Form(
      form.Dropdown('prefix', ['Mr.', 'Mrs.', 'Dr.', 'Ms.', 'Miss'],  description='Prefix'),
      form.Textbox('lname', form.Validator("Last name can't be blank", bool), size='16', description='Last Name'),
      form.Textbox('fname', form.Validator("First name can't be blank", bool),  size='16', description='First Name'),
      form.Textbox('email', form.notnull, form.regexp(email_regex, 'Please enter a valid email'), description='Email', size='30'),
      form.Textbox('addr1', form.Validator("Address can't be blank", bool), description='Address', size='20'),
      form.Textbox('addr2', description='Address', size='20'),
      form.Textbox('city', form.Validator("City can't be blank", bool), description='City'),
      form.Dropdown('state', getstates(), form.Validator("State can't be blank", bool), description='State'),
      form.Textbox('zipcode', form.Validator("Zip code can't be blank", bool), form.regexp(r'^[0-9]{5}$', 'Please enter a valid zip'),
                    size='5', maxlength='5', description='Zip'),
      form.Textbox('zip4', form.regexp(r'^$|[0-9]{4}', 'Please Enter a valid zip'),
                    size='4', maxlength='4',description=''),
      form.Textbox('phone', form.Validator("Phone can't be blank", bool), form.regexp(r'^[0-9-. ]*$', 'Please enter a valid phone number'), 
                    form.Validator('Please enter a valid phone number', check_len), size='15', description='Phone'),
      form.Textbox('ptitle', form.Validator("Title can't be blank", bool), description="Title:", size='80'),
      form.Textarea('msg', form.Validator("Description can't be blank", bool), description="Description:", rows='15', cols='80'),
      form.Textbox('captcha', pre='', description="Validation:"),
      form.Hidden('signid'),
      validators = [ZipValidator()]
      )

captcha = form.Textbox('captcha',
    form.Validator("Enter the letters as they are shown in the image", bool),
    size='10',
    description='Validation'
    )

signform = form.Form(
    form.Textbox('fname', form.notnull, description='First Name:', post=' *', size='17'),
    form.Textbox('lname', form.notnull, description='Last Name:', post=' *', size='17'),
    form.Textbox('email',
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:',
            post=' *',
            size='30'),
    form.Checkbox('share_with', value='off', description="Share my email with the author of this petition"),
    form.Textarea('comment', description='Personal comment (explain how this affects you):', cols=70, rows=4)
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
                rows=3,
                tabindex=1),
    form.Textbox('subject', form.notnull, description="Subject:", size='50', tabindex=2),
    form.Textarea('body', form.notnull, description="", cols=70, rows=12, tabindex=3)
    )

loadcontactsform = form.Form(
    form.Textbox('email',
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:',
            size='20'),
    form.Dropdown('provider',
            [(None, 'Select Provider'),
            ('google', 'Google'),
            ('yahoo', 'Yahoo'),
            ('msn', 'MSN/Hotmail')],
            form.notnull,
            description='')
    )

signupform = form.Form(
    form.Textbox('email',
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            form.Validator('An account with that email already exists', emailnotexists),
            description='Email'),
    form.Password('password', form.notnull, description='Password'),
    form.Password('password_again', form.notnull, description='Password again'),
    form.Hidden('redirect'),
    form.Hidden('state'),
    validators = [form.Validator('Oops, passwords don\'t match', lambda i: i.password == i.password_again)]
    )

loginform = form.Form(
    form.Textbox('useremail',
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email'),
    form.Password('password', form.notnull, description='Password'),
    form.Hidden('redirect'),
    form.Hidden('state'),
    validators = [form.Validator('Oops, wrong email or password', lambda i: bool(loginuser(i.useremail, i.password)))]
    )

forgot_password = form.Form(
    form.Textbox('email',
            form.notnull,
            form.regexp(email_regex, 'Please enter a valid email'),
            description='Email:'
            ),
    validators = [form.Validator("Account doesn't exist with this email", lambda i: not emailnotexists(i.email))]
    )

userinfo = form.Form(
        form.Dropdown('prefix', ['Mr.', 'Mrs.', 'Dr.', 'Ms.', 'Miss'], description='Prefix'),
        form.Textbox('fname', description='First Name'),
        form.Textbox('lname', description='Last Name'),
        form.Textbox('addr1', description='Address Line1', size='20'),
        form.Textbox('addr2', description='Address Line2', size='20'),
        form.Textbox('city', description='City'),
        form.Dropdown('state', getstates(), form.notnull, description='State'),
        form.Textbox('zip5', form.regexp(r'^$|[0-9]{5}', 'Please enter a valid zip'),
                         size='5', maxlength='5', description='Zip'),
        form.Textbox('zip4', form.regexp(r'^$|[0-9]{4}', 'Please Enter a valid zip'),
                         size='4', maxlength='4', description='Zip4'),
        form.Textbox('phone', form.regexp(r'^[0-9-. ]*$', 'Please enter a valid phone number'),
                    form.Validator('Please enter a valid phone number', check_len), maxlength='15', description='Phone')
        )

change_password = form.Form(
        form.Password('password', form.notnull, description="New Password:", size='10'),
        form.Password('password_again', form.notnull, description="Confirm Password:", size='10'),
        validators = [form.Validator("Passwords do not match.", lambda f: f.password == f.password_again)]
    )

curr_password = form.Password('curr_password',
            form.notnull,
            description='Current Password:',
            size='10'
            )
