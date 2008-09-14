import web

from settings import db


total_pop = ['/TotalPopulation/Total' ]


edu_totals = ['/Population25YearsAndOver/Female',
        '/Population25YearsAndOver/Male']
edu_college = [ 
        '/Population25YearsAndOver/Female/AssociateDegree',
        '/Population25YearsAndOver/Female/BachelorsDegree',
        '/Population25YearsAndOver/Female/DoctorateDegree',
        '/Population25YearsAndOver/Female/MastersDegree',
        '/Population25YearsAndOver/Female/ProfessionalSchoolDegree',
        '/Population25YearsAndOver/Female/SomeCollege1OrMoreYearsNoDegree',
        '/Population25YearsAndOver/Female/SomeCollegeLessThan1Year',

        '/Population25YearsAndOver/Male/AssociateDegree',
        '/Population25YearsAndOver/Male/BachelorsDegree',
        '/Population25YearsAndOver/Male/DoctorateDegree',
        '/Population25YearsAndOver/Male/MastersDegree',
        '/Population25YearsAndOver/Male/SomeCollege1OrMoreYearsNoDegree',
        '/Population25YearsAndOver/Male/SomeCollegeLessThan1Year',
        ]
edu_prof_degree = ['/Population25YearsAndOver/Male/ProfessionalSchoolDegree']
edu_nocollege = [
        '/Population25YearsAndOver/Male/NoSchoolingCompleted',
        '/Population25YearsAndOver/Male/NurseryTo4thGrade',
        '/Population25YearsAndOver/Male/5thAnd6thGrade',
        '/Population25YearsAndOver/Male/7thAnd8thGrade',
        '/Population25YearsAndOver/Male/9thGrade',
        '/Population25YearsAndOver/Male/10thGrade',
        '/Population25YearsAndOver/Male/11thGrade',
        '/Population25YearsAndOver/Male/12thGradeNoDiploma',
        '/Population25YearsAndOver/Male/HighSchoolGraduateincludesEquivalency',

        '/Population25YearsAndOver/Female/NoSchoolingCompleted',
        '/Population25YearsAndOver/Female/NurseryTo4thGrade',
        '/Population25YearsAndOver/Female/5thAnd6thGrade',
        '/Population25YearsAndOver/Female/7thAnd8thGrade',
        '/Population25YearsAndOver/Female/9thGrade',
        '/Population25YearsAndOver/Female/10thGrade',
        '/Population25YearsAndOver/Female/11thGrade',
        '/Population25YearsAndOver/Female/12thGradeNoDiploma',
        '/Population25YearsAndOver/Female/HighSchoolGraduateincludesEquivalency',
        ]


marital_stat_totals = [ '/Population15YearsAndOver/Male',
        '/Population15YearsAndOver/Female' ]
marital_stat_never_married = [ '/Population15YearsAndOver/Male/NeverMarried',
        '/Population15YearsAndOver/Female/NeverMarried']
marital_stat_divorced = [ '/Population15YearsAndOver/Male/Divorced',
        '/Population15YearsAndOver/Female/Divorced' ]


mil_totals = ['/Population18YearsAndOver/Total']
#mil_total = ['/Population18YearsAndOver/Male','/Population18YearsAndOver/Female']
mil_cur = [ '/Population18YearsAndOver/Male/18To64Years/InArmedForces',
        '/Population18YearsAndOver/Male/65YearsAndOver/InArmedForces',
        '/Population18YearsAndOver/Female/18To64Years/InArmedForces',
        '/Population18YearsAndOver/Female/65YearsAndOver/InArmedForces' ]
mil_vet = [ '/Population18YearsAndOver/Male/18To64Years/Civilian/Veteran',
        '/Population18YearsAndOver/Male/65YearsAndOver/Civilian/Veteran',
        '/Population18YearsAndOver/Female/18To64Years/Civilian/Veteran',
        '/Population18YearsAndOver/Female/65YearsAndOver/Civilian/Veteran' ]
mil_none = [ '/Population18YearsAndOver/Male/18To64Years/Civilian/Nonveteran',
        '/Population18YearsAndOver/Male/65YearsAndOver/Civilian/Nonveteran',
        '/Population18YearsAndOver/Female/18To64Years/Civilian/Nonveteran',
        '/Population18YearsAndOver/Female/65YearsAndOver/Civilian/Nonveteran' ]


born_totals = ['/TotalPopulation/Total'] 
born_native = ['/TotalPopulation/Native']
born_foreign = ['/TotalPopulation/ForeignBorn']


def query_census(location, hr_keys):
    # Use DISTINCT since some hr_keys map to multiple internal_keys (but should
    # have same value).
    #q = db.select('census', what='SUM(DISTINCT(value))', where=web.sqlors('hr_key=', hr_keys)+' AND location='+web.sqlquote(location))
    q = db.query('SELECT SUM(value) FROM (SELECT DISTINCT value, hr_key FROM census WHERE '+web.sqlors('hr_key=', hr_keys)+' AND district_id='+web.sqlquote(location)+') AS foo;')
    if not q: return None
    return q[0].sum


# This is for the population of 18 years and older.
def mil_service(location):
    tot = query_census(location, mil_totals)
    cur = query_census(location, mil_cur)
    vet = query_census(location, mil_vet)
    none = query_census(location, mil_none)
    return {'pct_mil_cur': cur / tot,
            'pct_mil_vet': vet / tot,
            'pct_mil_none': vet / tot,
            'mil_total': tot}


# This is for the entire population 
def born_locations(location):
    tot = query_census(location, born_totals)
    native = query_census(location, born_native)
    foreign = query_census(location, born_foreign)
    return {'pct_born_foreign': foreign / tot,
            'pct_born_native': native / tot,
            'born_total': tot}


# This is for the population of 15 years and older.
def marital_stat(location):
    tot = query_census(location, marital_stat_totals)
    never_married = query_census(location, marital_stat_never_married)
    divorced = query_census(location, marital_stat_divorced)
    return {'pct_never_married': never_married / tot,
            'pct_divorced': divorced / tot,
            'marital_stat_total': tot}


# This is for the population of 25 years and older.
def education(location):
    tot = query_census(location, edu_totals)
    some_college = query_census(location, edu_college)
    professional = query_census(location, edu_prof_degree)
    no_college = query_census(location, edu_nocollege)
    return {'pct_some_college': some_college / tot,
            'pct_professional': professional / tot,
            'pct_no_college': no_college / tot,
            'edu_total': tot}


# This is for the entire population 
def get_total_pop(location):
    tot = query_census(location, total_pop)
    return {'total_pop': tot}


if __name__ == "__main__":
    from pprint import pprint
    states = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 
    'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 
    'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 
    'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 
    'WA', 'WI', 'WV', 'WY']
    for state in states:
        print state
        pprint(education(state))
        pprint(marital_stat(state))
        pprint(mil_service(state))
        pprint(get_total_pop(state))

