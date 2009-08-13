import os
import hmac
import base64

import web
from config import secret_key
from settings import db

def urlify(s):
    """
    >>> urlify("What the !@#$%^ is going on here!?")
    'what-the--is-going-on-here'
    """
    s = s.lower()
    out = []
    for k in s:
        if k == " ": out.append('-')
        elif k.isalpha() or k.isdigit(): out.append(k)
    return ''.join(out)

def encrypt(msg, key=None):
    return hmac.new(key or secret_key, msg).hexdigest()

def setcookie(name, value, expires=''):
    encoded = value + '#@#' + encrypt(value)
    web.setcookie(name, encoded, expires)

def getcookie(name):
    encoded = web.cookies().get(name, '#@#')
    value, encrypt_value = encoded.split('#@#')
    if encrypt(value) == encrypt_value:
        return value

def deletecookie(name):
    web.setcookie(name, expires=-1)

def get_trackid(uid, pid):
    if not uid: return
    uid = str(uid)
    uid_pid = base64.urlsafe_b64encode(uid+pid[:10])
    return ':'.join([uid, uid_pid])

def check_trackid(tid, pid):
    try:
        uid, uid_pid = tid.split(':')
        uid_pid = base64.urlsafe_b64decode(str(uid_pid))
    except:
        return
    if uid_pid == uid + pid[:10]:
        return uid

def set_msg(msg, msg_type=None):
    if msg_type == 'error':
        msg += '$ERR$'
    elif msg_type == 'note':
        msg += '$NOTE$'    
    web.setcookie('wd_msg', msg)

def get_delete_msg():
    msg = web.cookies().get('wd_msg', None)
    web.setcookie('wd_msg', '', expires=-1)

    msg_type = None
    if msg:
        if msg.endswith('$ERR$'):
            msg_type = 'error'
            msg = msg[:-5]
        elif msg.endswith('$NOTE$'):
            msg_type = 'note'    
            msg = msg[:-6]
    return msg, msg_type

def get_loggedin_email():
    return getcookie('wd_login')

def get_unverified_email():
    return getcookie('wd_email')

def get_loggedin_userid():
    email = get_loggedin_email()
    user = get_user_by_email(email)
    return user and user.id
    
def get_unverified_userid():
    email = get_unverified_email()
    user = get_user_by_email(email)
    return user and user.id

def get_user_by_email(email):
    try:
        return db.select('users', where='email=$email', vars=locals())[0]
    except IndexError:
        return

def get_user_by_id(uid):
    try:
        return db.select('users', where='id=$uid', vars=locals())[0]
    except IndexError:
        return
    
def set_login_cookie(email):
    setcookie('wd_login', email)

def del_login_cookie():
    web.setcookie("wd_login", "", expires=-1)

def del_unverified_cookie():
    web.setcookie("wd_email", "", expires=-1)
    
def unverified_login(email, fname, lname):
    setcookie('wd_email', email)
    user = get_user_by_email(email)
    if user:
        return user.id
    return db.insert('users', fname=fname, lname=lname, email=email)

def is_verified(email):
    verified = db.select('users', where='email=$email and (verified=True or password is not null)', vars=locals())
    return bool(verified)

def query_param(param, default_value):
    d = {param:default_value}
    i = web.input(**d)
    return i.get(param)

def get_user():
    email = get_loggedin_email() or get_unverified_email()
    user = get_user_by_email(email)
    return user
    
def get_user_name():
    user = get_user()
    return (user.fname or user.email[:user.email.index('@')]) if user else ''

def format_name(name):
    if name.find(',') != -1:
      i = name.index(',')
      name = name[i+2:]+' '+name[0:i]
    return name

def date_range(dfrom, dto):
    if dfrom and dto and dfrom != dto:
        return 'from %s to %s' % (web.datestr(dfrom), web.datestr(dto))
    elif ((dfrom == dto) and dfrom) or dfrom or dto:
        return 'on %s' % web.datestr(dfrom or dto)
    else:
        return ''

eo_codes = web.storage(ded = {"1":"Deductible",
                    "2":"Not deductible",
                    "3":"Deductible by treaty"},

             foundation = {"00":"All organizations except 501(c)(3)",
                           "02":"Private operating foundation exempt from paying excise taxes on investment income",
                           "03":"Private operating foundation (other)",
                           "04":"Private non-operating foundation",
                           "09":"Suspense",
                           "10":"Church 170(b)(1)(A)(i)",
                           "11":"School 170(b)(1)(A)(ii)",
                           "12":"Hospital or medical research organization 170(b)(1)(A)(iii)",
                           "13":"Organization which operates for benefit of college or university and is owned or operated by a governmental unit 170(b)(1)(A)(iv)",
                           "14":"Governmental unit 170(b)(1)(A)(v)",
                           "15":"Organization which receives a substantial part of its support from a governmental unit or the general public 170(b)(1)(A)(vi)",
                           "16":"Organization that normally receives no more than one third of its support from gross investment income and unrelated business income and at the same time more than one third of its support from contributions, fees, and gross receipts related to exempt purposes. 509(a)(2)",
                           "17":"Organizations operated solely for the benefit of and in conjunction with organizations described in 10 through 16 above. 509(a)(3)",
                           "18":"Organization organized and operated to test for public safety509(a)(4)",
                           },

             category = {("01","1"):"Government Instrumentality",
                         ("02","1"):"Title Holding Corporation",
                         ("03","1"):"Charitable Organization",
                         ("03","2"):"Educational Organization",
                         ("03","3"):"Literary Organization",
                         ("03","4"):"Organization to Prevent Cruelty to Animals",
                         ("03","5"):"Organization to Prevent Cruelty to Children",
                         ("03","6"):"Organization for Public Safety Testing",
                         ("03","7"):"Religious Organization",
                         ("03","8"):"Scientific Organization",
                         ("04","1"):"Civic League",
                         ("04","2"):"Local Association of Employees",
                         ("04","3"):"Social Welfare Organization",
                         ("05","1"):"Agricultural Organization",
                         ("05","2"):"Horticultural Organization",
                         ("05","3"):"Labor Organization",
                         ("06","1"):"Board of Trade",
                         ("06","2"):"Business League",
                         ("06","3"):"Chamber of Commerce",
                         ("06","4"):"Real Estate Board",
                         ("07","1"):"Pleasure, Recreational, or Social Club",
                         ("08","1"):"Fraternal Beneficiary Society, Order or Association",
                         ("09","1"):"Voluntary Employees' Beneficiary Association (Non-Govt. Emps.)",
                         ("09","2"):"Voluntary Employees' Beneficiary Association (Govt. Emps.)",
                         ("10","1"):"Domestic Fraternal Societies and Associations",
                         ("11","1"):"Teachers Retirement Fund Assoc.",
                         ("12","1"):"Benevolent Life Insurance Assoc.",
                         ("12","2"):"Mutual Ditch or Irrigation Co.",
                         ("12","3"):"Mutual Cooperative Telephone Co.",
                         ("12","4"):"Organization Like Those on Three Preceding Lines",
                         ("13","1"):"Burial Association",
                         ("13","2"):"Cemetery Company",
                         ("14","1"):"Credit Union",
                         ("14","2"):"Other Mutual Corp. or Assoc.",
                         ("15","1"):"Mutual Insurance Company or Assoc. Other Than Life or Marine",
                         ("16","1"):"Corp. Financing Crop Operations",
                         ("17","1"):"Supplemental Unemployment Compensation Trust or Plan",
                         ("18","1"):"Employee Funded Pension Trust (Created Before 6/25/59)",
                         ("19","1"):"Post or Organization of War Veterans",
                         ("20","1"):"Legal Service Organization",
                         ("21","1"):"Black Lung Trust",
                         ("22","1"):"Multiemployer Pension Plan",
                         ("23","1"):"Veterans Assoc. Formed Prior to 1880",
                         ("24","1"):"Trust Described in Sect. 4049 of ERISA",
                         ("25","1"):"Title Holding Co. for Pensions, etc.",
                         ("26","1"):"State-Sponsored High Risk Health Insurance Organizations",
                         ("27","1"):"State-Sponsored Workers' Compensation Reinsurance",
                         ("40","1"):"Apostolic and Religious Org. (501(d))",
                         ("50","1"):"Cooperative Hospital Service Organization (501(e))",
                         ("60","1"):"Cooperative Service Organization of Operating Educational Organization (501(f))",
                         ("70","1"):"Child Care Organization (501(k))",
                         ("71","1"):"Charitable Risk Pool",
                         ("81","1"):"Qualified State-Sponsored Tuition Program ",
                         ("92","1"):"4947(a)(1) - Private Foundation (Form 990PF Filer)"},
             affiliation = {"1":"Central",
                            "2":"Intermediate",
                            "3":"Independent",
                            "6":"Central",
                            "7":"Intermediate",
                            "8":"Central",
                            "9":"Subordinate"},
             activity = {"000":"", #000 is NOT an officially defined code but is used in the records to indicate a NULL value
                         "001":"Church, synagogue, etc",
                         "002":"Association or convention of  churches",
                         "003":"Religious order",
                         "004":"Church auxiliary",
                         "005":"Mission",
                         "006":"Missionary activities",
                         "007":"Evangelism",
                         "008":"Religious publishing activities",
                         "029":"Other religious activities",
                         "030":"School, college, trade school, etc.",
                         "031":"Special school for the blind, handicapped, etc",
                         "032":"Nursery school",
                         "033":"Faculty group",
                         "034":"Alumni association or group",
                         "035":"Parent or parent teachers association",
                         "036":"Fraternity or sorority",
                         "037":"Other student society or group",
                         "038":"School or college athletic association",
                         "039":"Scholarships for children of employees",
                         "040":"Scholarships (other)",
                         "041":"Student loans",
                         "042":"Student housing activities",
                         "043":"Other student aid",
                         "044":"Student exchange with foreign country",
                         "045":"Student operated business",
                         "046":"Private school",
                         "059":"Other school related activities",
                         "060":"Museum, zoo, planetarium, etc.",
                         "061":"Library",
                         "062":"Historical site, records or reenactment",
                         "063":"Monument",
                         "064":"Commemorative event (centennial, festival, pageant, etc.)",
                         "065":"Fair",
                         "088":"Community theatrical group",
                         "089":"Singing society or group",
                         "090":"Cultural performances",
                         "091":"Art exhibit",
                         "092":"Literary activities",
                         "093":"Cultural exchanges with foreign country",
                         "094":"Genealogical activities",
                         "119":"Other cultural or historical activities",
                         "120":"Publishing activities",
                         "121":"Radio or television broadcasting",
                         "122":"Producing films",
                         "123":"Discussion groups, forums, panels lectures, etc.",
                         "124":"Study and research (nonscientific)",
                         "125":"Giving information or opinion (see also Advocacy)",
                         "126":"Apprentice training",
                         "149":"Other instruction and training",
                         "150":"Hospital",
                         "151":"Hospital auxiliary",
                         "152":"Nursing or convalescent home",
                         "153":"Care and housing for the aged (see also 382)",
                         "154":"Health clinic",
                         "155":"Rural medical facility",
                         "156":"Blood bank",
                         "157":"Cooperative hospital service organization",
                         "158":"Rescue and emergency service",
                         "159":"Nurses register or bureau",
                         "160":"Aid to the handicapped (see also 031)",
                         "161":"Scientific research (diseases)",
                         "162":"Other medical research",
                         "163":"Health insurance (medical, dental, optical, etc.)",
                         "164":"Prepared group health plan",
                         "165":"Community health planning",
                         "166":"Mental health care",
                         "167":"Group medical practice association",
                         "168":"Infaculty group practice association",
                         "169":"Hospital pharmacy, parking facility, food services, etc.",
                         "179":"Other health services",
                         "180":"Contact or sponsored scientific research for industry",
                         "181":"Scientific research for government",
                         "199":"Other scientific research activities",
                         "200":"Business promotion (chamber of commerce, business league, etc.	",
                         "201":"Real estate association",
                         "202":"Board of trade",
                         "203":"Regulating business",
                         "204":"Promotion of fair business practices",
                         "205":"Professional association",
                         "206":"Professional association auxiliary",
                         "207":"Industry trade shows",
                         "208":"Convention displays",
                         "209":"Research, development and testing",
                         "210":"Professional athletic league",
                         "211":"Underwriting municipal insurance",
                         "212":"Assigned risk insurance activities",
                         "213":"Tourist bureau",
                         "229":"Other business or professional group",
                         "230":"Farming",
                         "231":"Farm bureau",
                         "232":"Agricultural group",
                         "233":"Horticultural group",
                         "234":"Farmers cooperative marketing or purchasing",
                         "235":"Farmers cooperative marketing or purchasing",
                         "236":"Dairy herd improvement association",
                         "237":"Breeders association",
                         "249":"Other farming and related activities",
                         "250":"Mutual ditch, irrigation, telephone, electric company or like organization",
                         "251":"Credit union",
                         "252":"Reserve funds or insurance for domestic building and loan association, cooperative bank, or mutual savings bank",
                         "253":"Mutual insurance company",
                         "254":"Corporation organized under an Act of Congress (see also use (904)",
                         "259":"Other mutual organization",
                         "260":"Fraternal Beneficiary society, order, or association",
                         "261":"Improvement of conditions of workers",
                         "262":"Association of municipal employees",
                         "263":"Association of employees",
                         "264":"Employee or member welfare association",
                         "265":"Sick, accident, death, or similar benefits",
                         "266":"Strike benefits",
                         "267":"Unemployment benefits",
                         "268":"Pension or retirement benefits",
                         "269":"Vacation benefits",
                         "279":"Other services or benefits to members or employees",
                         "280":"Country club",
                         "281":"Hobby club",
                         "282":"Dinner club",
                         "283":"Variety club",
                         "284":"Dog club",
                         "285":"Women's club",
                         "286":"Hunting or fishing club",
                         "287":"Swimming or tennis club",
                         "288":"Other sports club",
                         "296":"Community center",
                         "297":"Community recreational facilities (park, playground, etc)",
                         "298":"Training in sports",
                         "299":"Travel tours",
                         "300":"Amateur athletic association",
                         "301":"Fundraising athletic or sports event",
                         "317":"Other sports or athletic activities",
                         "318":"Other recreational activities",
                         "319":"Other social activities",
                         "320":"Boy Scouts, Girl Scouts, etc.",
                         "321":"Boys Club, Little League, etc.",
                         "322":"FFA, FHA, 4H club, etc.",
                         "323":"Key club",
                         "324":"YMCA, YWCA, YMCA, etc.",
                         "325":"Camp",
                         "326":"Care and housing of children (orphanage, etc)",
                         "327":"Prevention of cruelty to children",
                         "328":"Combat juvenile delinquency",
                         "349":"Other youth organization or activities",
                         "350":"Preservation of natural resources (conservation)",
                         "351":"Combating or preventing pollution (air, water, etc)",
                         "352":"Land acquisition for preservation",
                         "353":"Soil or water conservation",
                         "354":"Preservation of scenic beauty",
                         "355":"Wildlife sanctuary or refuge",
                         "356":"Garden club",
                         "379":"Other conservation, environmental or beautification activities",
                         "380":"Lowincome housing",
                         "381":"Low and moderate income housing",
                         "382":"Housing for the aged (see also 153)",
                         "398":"Instruction and guidance on housing",
                         "399":"Other housing activities",
                         "400":"Area development, redevelopment of renewal",
                         "401":"Homeowners association",
                         "402":"Other activity aimed t combating community deterioration",
                         "403":"Attracting new industry or retaining industry in an area",
                         "404":"Community promotion",
                         "405":"Loans or grants for minority businesses",
                         "406":"Crime prevention",
                         "407":"Voluntary firemen's organization or auxiliary",
                         "408":"Community service organization",
                         "429":"Other inner city or community benefit activities",
                         "430":"Defense of human and civil rights",
                         "431":"Elimination of prejudice and discrimination (race, religion, sex, national origin, etc)",
                         "432":"Lessen neighborhood tensions",
                         "449":"Other civil rights activities",
                         "460":"Public interest litigation activities",
                         "461":"Other litigation or support of litigation",
                         "462":"Legal aid to indigents",
                         "463":"Providing bail",
                         "465":"Plan under IRC section 120",
                         "480":"Propose, support, or oppose legislation",
                         "481":"Voter information on issues or candidates",
                         "482":"Voter education (mechanics of registering, voting etc.)",
                         "483":"Support, oppose, or rate political candidates",
                         "484":"Provide facilities or services for political campaign activities",
                         "509":"Other legislative and political activities",
                         "510":"Firearms control",
                         "511":"Selective Service System",
                         "512":"National defense policy",
                         "513":"Weapons systems",
                         "514":"Government spending",
                         "515":"Taxes or tax exemption",
                         "516":"Separation of church and state",
                         "517":"Government aid to parochial schools",
                         "518":"U.S. foreign policy",
                         "519":"U.S. military involvement",
                         "520":"Pacifism and peace",
                         "521":"Economicpolitical system of U.S.",
                         "522":"Anticommunism",
                         "523":"Right to work",
                         "524":"Zoning or rezoning",
                         "525":"Location of highway or transportation system",
                         "526":"Rights of criminal defendants",
                         "527":"Capital punishment",
                         "528":"Stricter law enforcement",
                         "529":"Ecology or conservation",
                         "530":"Protection of consumer interests",
                         "531":"Medical care service",
                         "532":"Welfare systems",
                         "533":"Urban renewal",
                         "534":"Busing student to achieve racial balance",
                         "535":"Racial integration",
                         "536":"Use of intoxicating beverage",
                         "537":"Use of drugs or narcotics",
                         "538":"Use of tobacco",
                         "539":"Prohibition of erotica",
                         "540":"Sex education in public schools",
                         "541":"Population control",
                         "542":"Birth control methods",
                         "543":"Legalized abortion",
                         "559":"Other matters",
                         "560":"Supplying money, goods or services to the poor",
                         "561":"Gifts or grants to individuals (other than scholarships)",
                         "562":"Other loans to individuals",
                         "563":"Marriage counseling",
                         "564":"Family planning",
                         "565":"Credit counseling an assistance",
                         "566":"Job training, counseling, or assistance",
                         "567":"Draft counseling",
                         "568":"Vocational counseling",
                         "569":"Referral service (social agencies)",
                         "572":"Rehabilitating convicts or exconvicts",
                         "573":"Rehabilitating alcoholics, drug abusers, compulsive gamblers, etc.",
                         "574":"Day care center",
                         "575":"Services for the aged (see also 153 ad 382)",
                         "600":"Community Chest, United Way, etc.",
                         "601":"Booster club",
                         "602":"Gifts, grants, or loans to other organizations",
                         "603":"Nonfinancial services of facilities to other organizations",
                         "900":"Cemetery or burial activities",
                         "901":"Perpetual (care fund (cemetery, columbarium, etc)",
                         "902":"Emergency or disaster aid fund",
                         "903":"Community trust or component",
                         "904":"Government instrumentality or agency (see also 254)",
                         "905":"Testing products for public safety",
                         "906":"Consumer interest group",
                         "907":"Veterans activities",
                         "908":"Patriotic activities",
                         "909":"Non-exempt charitable trust described in section 4947(a)(1) of the Code",
                         "910":"Domestic organization with activities outside U.S.",
                         "911":"Foreign organization",
                         "912":"Title holding corporation",
                         "913":"Prevention of cruelty to animals",
                         "914":"Achievement pries of awards",
                         "915":"Erection or maintenance of public building or works",
                         "916":"Cafeteria, restaurant, snack bar, food services, etc.",
                         "917":"Thrift ship, retail outlet, etc.",
                         "918":"Book, gift  or supply store",
                         "919":"Advertising",
                         "920":"Association of employees",
                         "921":"Loans or credit reporting",
                         "922":"Endowment fund or financial services",
                         "923":"Indians (tribes, cultures, etc.)",
                         "924":"Traffic or tariff bureau",
                         "925":"Section 501(c)(1) with 50% deductibility",
                         "926":"Government instrumentality other than section 501(c)",
                         "927":"Fundraising",
                         "928":"4947(a)(2) trust",
                         "930":"Prepaid legal services pan exempt under IRC section 501(c)(20)",
                         "931":"Withdrawal liability payment fund",
                         "990":"Section 501(k) child care organization",
                         "994":"Described in section 170(b)1)(a)(vi) of the Code",
                         "995":"Described in section 509(a)(2) of the Code",
                         "998":"Denied or failed to establish it's exempt status.  Will be updated when status is granted"},
             org = {"1":"Corporation",
                    "2":"Trust",
                    "3":"Cooperative",
                    "4":"Partnership",
                    "5":"Association"},
             exempt = { "01":"Unconditional Exemption",
                        "02":"Conditional Exemption",
                        "12":"Trust described in section 4947(a)(2) of the IR Code",
                        "25":"Organization terminating its private foundation status under section507(b)(1)(B) of the Code",
                        "32":"Organization that did not respond to an IRS CP 140 notice requesting information on its continued exempt status",
                        },
             income = {"0":"0",
                       "1":"1   to   9,999",
                       "2":"10,000   to   24,999",
                       "3":"25,000   to   99,999",
                       "4":"100,000   to   499,999",
                       "5":"500,000   to   999,999",
                       "6":"1,000,000   to   4,999,999",
                       "7":"5,000,000   to   9,999,999",
                       "8":"10,000,000   to   49,999,999",
                       "9":"50,000,000   and   greater"
                       },

             fr1 = {"03":"990 - Group return",
                    "07":"990 - Government 501(c)(1)",
                    "01":"990 (all other) or 990EZ return",
                    "02":"990 - Not required to file Form 990 (income less than $25,000)",
                    "06":"990 - Not required to file (church) ",
                    "13":"990 - Not required to file (religious organization)",
                    "14":"990 - Not required to file (instrumentalities of states or political subdivisions)",
                    "00":"990 - Not required to file(all other)"
                    },

             fr2 = {"1":"990-PF return",
                    "0":"No 990-PF return"
                    }

             )


g = web.template.Template.globals
g['slice'] = slice
g['commify'] = web.commify
g['int'] = int
g['round'] = round
g['abs'] = abs
g['len'] = len
g['changequery'] = web.changequery
g['enumerate'] = enumerate
g['datestr'] = web.datestr
g['urlquote'] = web.urlquote
g['format_name'] = format_name
g['date_range'] = date_range
g['getattr'] = getattr

g['query_param'] = query_param
g['is_logged_in'] = lambda: bool(get_loggedin_email() or get_unverified_email())

import markdown
g['format'] = markdown.markdown

import blog
g['blog_content'] = blog.content

import re
r_html = re.compile(r'<[^>]+?>')
def striphtml(x):
    return r_html.sub('', x).replace('\n', ' ')
g['striphtml'] = striphtml
g['getpath'] = lambda : web.ctx.homepath + web.ctx.path
g['getfullpath'] = lambda : web.ctx.homepath + web.ctx.fullpath

g['cookies_on'] = lambda : True #bool(web.cookies().get('webpy_session_id')) #@@@ fix this
g['get_user_id'] = lambda: get_loggedin_userid() or get_unverified_userid()
g['get_user_name'] = get_user_name
