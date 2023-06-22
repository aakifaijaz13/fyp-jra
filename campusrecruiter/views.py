import io
import json
import zipfile
from random import randint, randrange

import requests
from django.db.models import Max, Q, query, QuerySet, Avg
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .models import *
from django.contrib.auth import login, logout, authenticate
from datetime import datetime, timedelta, time
from datetime import date
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .helper import send_email, send_email_async
import re
from twilio.rest import Client


# Create your views here.

def index(request):
    vacancy = Vacancy.objects.all()
    return render(request, 'index.html', locals())


def jobDetails(request, pid):
    vacancy = Vacancy.objects.get(id=pid)
    return render(request, 'jobDetails.html', locals())


# ===================== Candidate View Here =====================

def candidate(request):
    studentid = 1001 if Candidate.objects.count() == 0 else Candidate.objects.aggregate(max=Max('StudentID'))["max"] + 1

    if request.method == 'POST' and User.objects.filter(username=request.POST['email']).exists():
        error = ""
        if request.method == 'POST':
            e = request.POST['email']
            p = request.POST['password']
            last_login = User.objects.get(username=e).last_login
            date_joind = User.objects.get(username=e).date_joined
            user = authenticate(username=e, password=p)
            if last_login is not None:
                serialized_datetime = last_login.isoformat()
                my_data = {"datetime": serialized_datetime}
                serialized_data = json.dumps(my_data)
                request.session['last_login'] = serialized_data

            try:
                if user:
                    login(request, user)
                    if (user.last_login is None or user.date_joined is None) or (
                            last_login - date_joind).total_seconds() < 60:
                        send_email_to(user.email, f"{user.first_name}  {user.last_name}", request,
                                      Candidate.objects.get(user=user).StudentID)

                    error1 = "no"
                else:
                    error1 = "yes"
            except:
                error1 = "yes"

    else:
        if request.method == "POST":
            fname = request.POST['FirstName']
            lname = request.POST['LastName']
            mob = request.POST['MobileNumber']
            gender = request.POST['Gender']
            email = request.POST['email']
            pwd = request.POST['password']
            std = request.POST['StudentID']
            print(fname, lname)
            try:
                user = User.objects.create_user(username=email, password=pwd, first_name=fname, last_name=lname)
                Candidate.objects.create(user=user, StudentID=std, MobileNumber=mob, Gender=gender)
                error = "no"
            except:
                error = "yes"
            send_email_to(email, f"{fname}  {lname}", request, std)

    return render(request, 'candidate.html', locals())


def send_email_to(email, name, request, studentid):
    scheme = request.scheme
    host = request.META['HTTP_HOST']
    base_url = '{}://{}'.format(scheme, host)
    base_url = f"{base_url}/addWorkDetails/{studentid}"
    recipient_list = [email]
    subject = 'Work Form'
    message = f"Hi {name}! \nKindly fill the form to get the jobs according to your skills, " \
              f"preferences and work experience \n\n Link: {base_url}"
    send_email(subject, message, recipient_list)


def get_vacancy(user, last_login):
    vacancies = []
    for i in Vacancy.objects.all():
        if i.ApplyDate >= last_login.date():
            vacancies.append(i.JobTitle)
    return vacancies


def canDashboard(request):
    if not request.user.is_authenticated:
        return redirect('candidate')

    user = request.user
    candidates = Candidate.objects.get(user=user)

    today = datetime.now().date()
    yesterday = today - timedelta(1)
    lasts = today - timedelta(7)

    todayapply = Applyjob.objects.filter(ApplyDate=today, candidate=candidates).count()
    yesterdayapply = Applyjob.objects.filter(ApplyDate=yesterday, candidate=candidates).count()
    lastsevendayapply = Applyjob.objects.filter(ApplyDate=lasts, candidate=candidates).count()
    totalapply = Applyjob.objects.filter(candidate=candidates).count()
    totalvacancy = Vacancy.objects.all().count()

    if 'last_login' in request.session:
        last_login = json.loads(request.session['last_login'])
        serialized_datetime = last_login["datetime"]
        my_datetime = datetime.fromisoformat(serialized_datetime)
        last_login = my_datetime + timedelta(hours=5)
        print(last_login)
        notification = get_vacancy(user, last_login)

    return render(request, 'canDashboard.html', locals())


def studentProfile(request):
    if not request.user.is_authenticated:
        return redirect('candidate')

    user = User.objects.get(id=request.user.id)
    candidate = Candidate.objects.get(user=user)

    if request.method == "POST":
        fname = request.POST['firstName']
        lname = request.POST['lastName']
        MobileNumber = request.POST['MobileNumber']
        Gender = request.POST['Gender']
        Age = request.POST['Age']
        DOB = request.POST['DOB']

        candidate.user.first_name = fname
        candidate.user.last_name = lname
        candidate.MobileNumber = MobileNumber
        candidate.Gender = Gender
        candidate.Age = Age
        candidate.DOB = DOB

        try:
            candidate.save()
            candidate.user.save()
            error = "no"
        except:
            error = "yes"

        try:
            Image = request.FILES['Image']
            candidate.Image = Image
            candidate.save()
        except:
            pass
    return render(request, 'studentProfile.html', locals())


def addFormDetail(request):
    if not request.user.is_authenticated:
        return redirect('candidate')
    user = request.user
    try:
        education = Education.objects.get(user=user)
    except:
        pass
    try:

        user = User.objects.get(id=request.user.id)
        candidates = Candidate.objects.get(user=user)

        error = ""
        if request.method == "POST":
            secondaryBoard = request.POST['SecondaryBoard']
            secondaryBoardyop = request.POST['SecondaryBoardyop']
            secondaryBoardper = request.POST['SecondaryBoardper']
            secondaryBoardcgpa = request.POST['SecondaryBoardcgpa']
            sSecondaryBoard = request.POST['SSecondaryBoard']
            sSecondaryBoardyop = request.POST['SSecondaryBoardyop']
            sSecondaryBoardper = request.POST['SSecondaryBoardper']
            sSecondaryBoardcgpa = request.POST['SSecondaryBoardcgpa']
            graUni = request.POST['GraUni']
            graUniyop = request.POST['GraUniyop']
            graUnidper = request.POST['GraUnidper']
            graUnicgpa = request.POST['GraUnicgpa']
            pGUni = request.POST['PGUni']
            PGUniyop = request.POST['PGUniyop']
            PGUniper = request.POST['PGUniper']
            PGUnicgpa = request.POST['PGUnicgpa']
            ExtraCurriculars = request.POST['ExtraCurriculars']
            OtherAchivement = request.POST['OtherAchivement']

            try:
                Education.objects.create(user=user,
                                         SecondaryBoard=secondaryBoard, SecondaryBoardyop=secondaryBoardyop,
                                         SecondaryBoardper=secondaryBoardper, SecondaryBoardcgpa=secondaryBoardcgpa,
                                         SSecondaryBoard=sSecondaryBoard, SSecondaryBoardyop=sSecondaryBoardyop,
                                         SSecondaryBoardper=sSecondaryBoardper, SSecondaryBoardcgpa=sSecondaryBoardcgpa,
                                         GraUni=graUni, GraUniyop=graUniyop, GraUnidper=graUnidper,
                                         GraUnicgpa=graUnicgpa,
                                         PGUni=pGUni, PGUniyop=PGUniyop, PGUniper=PGUniper, PGUnicgpa=PGUnicgpa,
                                         ExtraCurriculars=ExtraCurriculars, OtherAchivement=OtherAchivement)
                error = "no"
            except:
                error = "yes"
    except:
        pass
    return render(request, 'addFormDetail.html', locals())


def manageFormDetail(request):
    if not request.user.is_authenticated:
        return redirect('candidate')

    user = request.user
    try:
        education = Education.objects.get(user=user)
    except:
        pass

    if request.method == "POST":
        SecondaryBoard = request.POST['SecondaryBoard']
        SecondaryBoardyop = request.POST['SecondaryBoardyop']
        SecondaryBoardper = request.POST['SecondaryBoardper']
        SecondaryBoardcgpa = request.POST['SecondaryBoardcgpa']

        SSecondaryBoard = request.POST['SSecondaryBoard']
        SSecondaryBoardyop = request.POST['SSecondaryBoardyop']
        SSecondaryBoardper = request.POST['SSecondaryBoardper']
        SSecondaryBoardcgpa = request.POST['SSecondaryBoardcgpa']

        GraUni = request.POST['GraUni']
        GraUniyop = request.POST['GraUniyop']
        GraUnidper = request.POST['GraUnidper']
        GraUnicgpa = request.POST['GraUnicgpa']

        PGUni = request.POST['PGUni']
        PGUniyop = request.POST['PGUniyop']
        PGUniper = request.POST['PGUniper']
        PGUnicgpa = request.POST['PGUnicgpa']

        ExtraCurriculars = request.POST['ExtraCurriculars']
        OtherAchivement = request.POST['OtherAchivement']

        education.SecondaryBoard = SecondaryBoard
        education.SecondaryBoardyop = SecondaryBoardyop
        education.SecondaryBoardper = SecondaryBoardper
        education.SecondaryBoardcgpa = SecondaryBoardcgpa

        education.SSecondaryBoard = SSecondaryBoard
        education.SSecondaryBoardyop = SSecondaryBoardyop
        education.SSecondaryBoardper = SSecondaryBoardper
        education.SSecondaryBoardcgpa = SSecondaryBoardcgpa

        education.GraUni = GraUni
        education.GraUniyop = GraUniyop
        education.GraUnidper = GraUnidper
        education.GraUnicgpa = GraUnicgpa

        education.PGUni = PGUni
        education.PGUniyop = PGUniyop
        education.PGUniper = PGUniper
        education.PGUnicgpa = PGUnicgpa

        education.ExtraCurriculars = ExtraCurriculars
        education.OtherAchivement = OtherAchivement

        try:
            education.save()
            error = "no"
        except:
            error = "yes"
    return render(request, 'manageFormDetail.html', locals())


def workDetails(request, student_id):
    candidate = Candidate.objects.get(StudentID=student_id)
    user_name = candidate.user.username.split('.')[0]
    user = User.objects.get(username=candidate.user.username)
    try:
        candidate = Candidate.objects.get(user=user)
        work_experience = WorkExperience.objects.get(candidate=candidate)
    except:
        pass
    if request.method == "POST":
        YearsOfExperience = request.POST['YearsOfExperience']
        Skills = request.POST['Skills']
        Preferences = request.POST['Preferences']
        Location = request.POST['Location']
        try:
            WorkExperience.objects.create(experience=YearsOfExperience, candidate=candidate, skills=Skills,
                                          preferences=Preferences, location=Location)
            error = "no"
            redirect('candidate')
        except:
            error = "yes"
    return render(request, 'addWorkDetails.html', locals())


def manageWorkDetails(request):
    if not request.user.is_authenticated:
        return redirect('candidate')

    user = request.user
    try:
        candidate = Candidate.objects.get(user=user)
        work_experience = WorkExperience.objects.get(candidate=candidate)
    except:
        pass

    if request.method == "POST":
        YearsOfExperience = request.POST['YearsOfExperience']
        Skills = request.POST['Skills']
        Preferences = request.POST['Preferences']
        Location = request.POST['Location']
        try:
            work_experience.experience = YearsOfExperience
            work_experience.preferences = Preferences
            work_experience.skills = Skills
            work_experience.candidate = candidate
            work_experience.location = Location
            work_experience.save()
            error = "no"
        except:
            error = "yes"
    return render(request, 'manageWorkDetails.html', locals())


def viewVacancy(request):
    if not request.user.is_authenticated:
        return redirect('candidate')
    vacancy = Vacancy.objects.all()
    vacancies = Vacancy.objects.all()

    user = request.user
    candidate = Candidate.objects.get(user=user)
    work_experience = WorkExperience.objects.filter(candidate=candidate)
    appliedjob = Applyjob.objects.filter(candidate=candidate)
    recommend = []
    if work_experience.count() > 0:
        recommendation = get_jobs_for_recommandation(candidate, vacancy)
        recommendation = sorted(recommendation, key=lambda k: k['score'], reverse=True)
        print(recommendation)
        if len(recommendation) < 10:
            for x in range(len(recommendation)):
                recommend.append(recommendation[x]['vacancy'])
        else:
            for x in range(0, 10):
                recommend.append(recommendation[x]['vacancy'])

    recommend_size = len(recommend)
    li = []
    locations = []
    locations.append("All")
    for i in appliedjob:
        li.append(i.vacancy.id)
    for i in vacancy:
        locations.append(i.JobLocation.title())
    locations = list(set(locations))
    locations.sort()

    return render(request, 'viewVacancy.html', locals())


def custom_tokenizer(text):
    return [text]


def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search


def get_jobs_for_recommandation(candidate, vacancy):
    work_experience = WorkExperience.objects.get(candidate=candidate)
    candidate_skills = work_experience.skills.split(',')
    candidate_preferences = work_experience.preferences.split(',')
    candidate_experience = work_experience.experience
    candidate_location = work_experience.location
    candidate_skills_md = []
    for a in candidate_skills:
        candidate_skills_md.append(a.strip().lower())
    candidate_preferences_md = []
    for a in candidate_preferences:
        candidate_preferences_md.append(a.strip().lower())

    matching_vacancies = []
    for v in vacancy:
        scores = []
        for skill in candidate_skills_md:
            if findWholeWord(skill)(v.JobTitle.lower()) is not None:
                scores.append(1)
            else:
                scores.append(0)

        if (sum(scores) / len(scores)) > 0:
            for skill in candidate_skills_md:
                if findWholeWord(skill)(v.JobDescriptions.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

            for preferences in candidate_preferences_md:
                if findWholeWord(preferences)(v.JobTitle.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

                if findWholeWord(preferences)(v.JobDescriptions.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

            if candidate_experience in v.JobDescriptions:
                scores.append(1)
            else:
                scores.append(0)

            if candidate_location.lower() is not None and v.JobLocation.lower() == candidate_location.lower():
                scores.append(2.0)
            else:
                scores.append(0.0)
        else:
            scores.append(0.0)

        avg_score = sum(scores) / len(scores)
        if avg_score > 0:
            d = {'score': avg_score, 'vacancy': v}
            matching_vacancies.append(d)
    return matching_vacancies


def viewVacancyDetails(request, pid):
    if not request.user.is_authenticated:
        return redirect('candidate')

    vacancy = Vacancy.objects.get(id=pid)

    user = User.objects.get(id=request.user.id)
    candidates = Candidate.objects.get(user=user)

    date1 = date.today()
    if vacancy.LastDate < date1:
        error = "close"
    elif vacancy.ApplyDate > date1:
        error = "notopen"
    else:
        if request.method == "POST":
            resume = request.FILES['Resume']
            Applyjob.objects.create(vacancy=vacancy, candidate=candidates, Resume=resume, ApplyDate=date.today(), Recommanded=recomeded_for_the_job(candidates, vacancy))
            error = "done"
    return render(request, 'viewVacancyDetails.html', locals())


def recomeded_for_the_job(candidate, vacancy):
    work_experience = WorkExperience.objects.filter(candidate=candidate)
    if work_experience.count() > 0:
        work_experience = work_experience[0]
        candidate_skills = work_experience.skills.split(',')
        candidate_preferences = work_experience.preferences.split(',')
        candidate_experience = work_experience.experience
        candidate_location = work_experience.location
        candidate_skills_md = []
        for a in candidate_skills:
            candidate_skills_md.append(a.strip().lower())
        candidate_preferences_md = []
        for a in candidate_preferences:
            candidate_preferences_md.append(a.strip().lower())

        scores = []
        for skill in candidate_skills_md:
            if findWholeWord(skill)(vacancy.JobTitle.lower()) is not None:
                scores.append(1)
            else:
                scores.append(0)

        if (sum(scores) / len(scores)) > 0:
            for skill in candidate_skills_md:
                if findWholeWord(skill)(vacancy.JobDescriptions.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

            for preferences in candidate_preferences_md:
                if findWholeWord(preferences)(vacancy.JobTitle.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

                if findWholeWord(preferences)(vacancy.JobDescriptions.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

            if candidate_experience in vacancy.JobDescriptions:
                scores.append(1)
            else:
                scores.append(0)

            if candidate_location.lower() is not None and vacancy.JobLocation.lower() == candidate_location.lower():
                scores.append(2.0)
            else:
                scores.append(0.0)
        else:
            scores.append(0.0)

        avg_score = sum(scores) / len(scores)
        return avg_score > 0
    else:
        return False


def historyofAppliedJob(request):
    if not request.user.is_authenticated:
        return redirect('candidate')
    user = request.user
    candidates = Candidate.objects.get(user=user)
    applyjob = Applyjob.objects.filter(candidate=candidates)
    return render(request, 'historyofAppliedJob.html', locals())


def viewHistoryAppliedjob(request, pid):
    if not request.user.is_authenticated:
        return redirect('candidate')

    applyjob = Applyjob.objects.get(id=pid)

    message = Message.objects.filter(appjob=applyjob)
    applyjobid = applyjob.id
    msgcount = Message.objects.filter(appjob=applyjob).count()
    return render(request, 'viewHistoryAppliedjob.html', locals())


def viewEducationDtls(request, pid):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = User.objects.get(id=pid)
    education = Education.objects.get(user=user)
    return render(request, 'viewEducationDtls.html', locals())


def candbetweenDateReport(request):
    if not request.user.is_authenticated:
        return redirect('candidate')

    user = request.user
    candidates = Candidate.objects.get(user=user)

    if request.method == "POST":
        fd = request.POST['FromDate']
        td = request.POST['ToDate']

        applyjob = Applyjob.objects.filter(Q(ApplyDate__gte=fd) & Q(ApplyDate__lte=td), candidate=candidates)
        return render(request, 'canbetweenReportDtls.html', locals())
    return render(request, 'candbetweenDateReport.html', locals())


def candidateSearchCategory(request):
    if not request.user.is_authenticated:
        return redirect('candidate')
    sd = None
    jobs = []
    for x in Vacancy.objects.all():
        jobs.append(x.JobTitle.title())
    jobs = list(set(jobs))
    jobs.sort()

    if request.method == 'POST':
        categories = {
            "entry": [],
            "mid": [],
            "senior": [],
        }
        sl = request.POST["searchCategory"]
        avg_salaries = {
            'Entry Level': Vacancy.objects.filter(Q(JobTitle__icontains=sl) & Q(Category__icontains="Entry")).aggregate(
                Avg('MonthlySalary'))['MonthlySalary__avg'],
            'Mid Level':
                Vacancy.objects.filter(Q(JobTitle__icontains=sl) & Q(Category__icontains="Mid")).aggregate(
                    Avg('MonthlySalary'))['MonthlySalary__avg'],
            'Senior Level':
                Vacancy.objects.filter(Q(JobTitle__icontains=sl) & Q(Category__icontains="Senior")).aggregate(
                    Avg('MonthlySalary'))['MonthlySalary__avg']
        }
        avg_salaries = {k: v for k, v in avg_salaries.items() if v is not None}
        print(avg_salaries)

    return render(request, 'candidateSearchCategory.html', locals())


def candidateChangePwd(request):
    if not request.user.is_authenticated:
        return redirect('candidate')
    error = ""
    user = request.user
    if request.method == "POST":
        o = request.POST['oldpassword']
        n = request.POST['newpassword']
        try:
            u = User.objects.get(id=request.user.id)
            if user.check_password(o):
                u.set_password(n)
                u.save()
                error = "no"
            else:
                error = 'not'
        except:
            error = "yes"
    return render(request, 'candidateChangePwd.html', locals())


# =========================== Employers Views Here ===========================

def employees(request):
    try:

        if request.method == "POST":

            comname = request.POST['CompanyName']
            conperson = request.POST['ContactPerson']
            email = request.POST.get('email')
            print(email)
            pwd = request.POST['password']
            mob = request.POST['MobileNumber']
            comurl = request.POST['CompanyUrl']
            comaddress = request.POST['CompanyAddress']
            comlogo = request.FILES['CompanyLogo']
            comCard = request.FILES['CompanyCard']

            try:
                user = User.objects.create_user(username=email, password=pwd, first_name=comname)
                Company.objects.create(user=user, ContactPerson=conperson, MobileNumber=mob, CompanyUrl=comurl,
                                       CompanyAddress=comaddress, CompanyLogo=comlogo, ComapnyCard=comCard,
                                       Approved=False)
                error = "no"
            except:
                error = "yes"
    except:
        if request.method == 'POST':
            e = request.POST['email']
            p = request.POST['password']
            user = authenticate(username=e, password=p)
            company = Company.objects.filter(user=user)
            try:
                if user and company[0].Approved == 'True':
                    login(request, user)
                    error1 = "no"
                elif company[0].Approved == 'False':
                    error2 = "yes"
                else:
                    error1 = "yes"
            except:
                error1 = "yes"
    return render(request, 'employees.html', locals())


@csrf_exempt
def verify(request):
    # Decode the bytes to a string
    string = request.body.decode('utf-8')
    # Parse the string as JSON to a dictionary
    data_dict = json.loads(string)
    type = data_dict['type']
    code = randrange(1000, 9999)
    now = datetime.now()
    if type == 'sms':
        number = data_dict['number']
        print(number)
        account_sid = 'AC9870b653df1a97b6db82c18f7e910ff4'
        auth_token = '8600c40830f08e04c4c7e8a5fcd91023'
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_='+14028210672',
            body=f'Your Verification Code is {code}',
            to=number
        )
        print(message)
    else:
        email = data_dict['email']
        subject = 'Recommended Job'
        message = f"Your Verification Code is {code}"
        send_email_async(subject, message, [email])
    return JsonResponse({'time': now, 'code': code})


def empDashboard(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = request.user
    company = Company.objects.get(user=user)
    vacancy = Vacancy.objects.filter(companies=company)

    totalvacancy = Vacancy.objects.filter(companies=company).count()
    # vacancy = Vacancy.objects.filter(companies=company)
    totalapp = Applyjob.objects.filter(vacancy__in=vacancy).count()
    totalNewapp = Applyjob.objects.filter(vacancy__in=vacancy, Status__isnull=True).count()
    totalSelectapp = Applyjob.objects.filter(vacancy__in=vacancy, Status='Sorted').count()
    totalRejectapp = Applyjob.objects.filter(vacancy__in=vacancy, Status='Rejected').count()

    return render(request, 'employee/empDashboard.html', locals())


def comProfile(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = User.objects.get(id=request.user.id)
    company = Company.objects.get(user=user)

    if request.method == "POST":
        comname = request.POST['CompanyName']
        conperson = request.POST['ContactPerson']
        mob = request.POST['MobileNumber']
        comurl = request.POST['CompanyUrl']
        comaddress = request.POST['CompanyAddress']

        company.user.first_name = comname
        company.ContactPerson = conperson
        company.MobileNumber = mob
        company.CompanyUrl = comurl
        company.CompanyAddress = comaddress

        try:
            company.save()
            company.user.save()
            error = "no"
        except:
            error = "yes"

        try:
            comlogo = request.FILES['CompanyLogo']
            company.CompanyLogo = comlogo
            company.save()
        except:
            pass
    return render(request, 'employee/comProfile.html', locals())


def addVacancy(request):
    if not request.user.is_authenticated:
        return redirect('employees')

    user = User.objects.get(id=request.user.id)
    company = Company.objects.get(user=user)
    newVacany = Vacancy.objects.filter(companies=company)

    if request.method == "POST":
        JobTitle = request.POST['JobTitle']
        MonthlySalary = request.POST['MonthlySalary']
        JobDescriptions = request.POST['JobDescriptions']
        Category = request.POST['Category']
        JobLocation = request.POST['JobLocation']
        NoofOpenings = request.POST['NoofOpenings']
        ApplyDate = request.POST['ApplyDate']
        LastDate = request.POST['LastDate']

        try:
            vc = Vacancy.objects.create(companies=company, Category=Category,
                                        JobTitle=JobTitle, MonthlySalary=MonthlySalary,
                                        JobDescriptions=JobDescriptions, JobLocation=JobLocation,
                                        NoofOpenings=NoofOpenings, ApplyDate=ApplyDate, LastDate=LastDate)
            error = "no"
            vacancy = Vacancy.objects.filter(id=vc.pk)
            for x in Candidate.objects.all():
                if WorkExperience.objects.filter(candidate=x).count() > 0:
                    send_email_for_recommandation(x, vacancy)
        except:
            error = "yes"

    return render(request, 'employee/addVacancy.html', locals())


def send_email_for_recommandation(candidate, vacancy):
    work_experience = WorkExperience.objects.get(candidate=candidate)
    candidate_skills = work_experience.skills.split(',')
    candidate_preferences = work_experience.preferences.split(',')
    candidate_experience = work_experience.experience
    candidate_location = work_experience.location
    candidate_skills_md = []
    for a in candidate_skills:
        candidate_skills_md.append(a.strip().lower())
    candidate_preferences_md = []
    for a in candidate_preferences:
        candidate_preferences_md.append(a.strip().lower())

    for v in vacancy:
        scores = []
        for skill in candidate_skills_md:
            if findWholeWord(skill)(v.JobTitle.lower()) is not None:
                scores.append(1)
            else:
                scores.append(0)

        if (sum(scores) / len(scores)) > 0:
            for skill in candidate_skills_md:
                if findWholeWord(skill)(v.JobDescriptions.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

            for preferences in candidate_preferences_md:
                if findWholeWord(preferences)(v.JobTitle.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

                if findWholeWord(preferences)(v.JobDescriptions.lower()) is not None:
                    scores.append(1)
                else:
                    scores.append(0)

            if candidate_experience in v.JobDescriptions:
                scores.append(1)
            else:
                scores.append(0)

            if candidate_location.lower() is not None and v.JobLocation.lower() == candidate_location.lower():
                scores.append(2.0)
            else:
                scores.append(0.0)
        else:
            scores.append(0.0)

        avg_score = sum(scores) / len(scores)
        if avg_score > 0:
            base_url = f"http:127.0.0.1:8000/viewVacancy"
            recipient_list = [candidate.user.username]
            subject = 'Recommended Job'
            message = f"Hi {candidate.user.first_name}! \nHere is the recommended job for you according to your work experience\n\n" \
                      f"Job Title: {v.JobTitle}\n" \
                      f"Job Description: {v.JobDescriptions}\n" \
                      f"Job Location: {v.JobLocation}\n" \
                      f"\nVisit the {base_url} Now to see the recommended jobs for you"
            send_email_async(subject, message, recipient_list)


def manageVacancy(request):
    if not request.user.is_authenticated:
        return redirect('employees')

    user = request.user
    company = Company.objects.get(user=user)
    vacancy = Vacancy.objects.filter(companies=company)

    return render(request, 'employee/manageVacancy.html', locals())


def editVacancy(request, pid):
    if not request.user.is_authenticated:
        return redirect('employees')
    error = ""
    company = Company.objects.all()
    vacancy = Vacancy.objects.get(id=pid)

    if request.method == "POST":
        JobTitle = request.POST['JobTitle']
        MonthlySalary = request.POST['MonthlySalary']
        JobDescriptions = request.POST['JobDescriptions']
        Category = request.POST['Category']
        JobLocation = request.POST['JobLocation']
        NoofOpenings = request.POST['NoofOpenings']
        ApplyDate = request.POST['ApplyDate']
        LastDate = request.POST['LastDate']

        vacancy.JobTitle = JobTitle
        vacancy.MonthlySalary = MonthlySalary
        vacancy.JobDescriptions = JobDescriptions
        vacancy.JobLocation = JobLocation
        vacancy.NoofOpenings = NoofOpenings
        vacancy.ApplyDate = ApplyDate
        vacancy.LastDate = LastDate
        vacancy.Category = Category

        try:
            vacancy.save()
            error = "no"
        except:
            error = "yes"
    return render(request, 'employee/editVacancy.html', locals())


def deleteVacancy(request, pid):
    if not request.user.is_authenticated:
        return redirect('employees')
    vacancy = Vacancy.objects.get(id=pid)
    vacancy.delete()
    return redirect('manageVacancy')


def newApplication(request):
    if not request.user.is_authenticated:
        return redirect('employees')

    user = request.user
    company = Company.objects.get(user=user)

    vacancy = [i.id for i in Vacancy.objects.filter(companies=company)]
    applyjob = Applyjob.objects.filter(vacancy__in=vacancy, Status=None)

    return render(request, 'employee/newApplication.html', locals())


def sortListedApplication(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = request.user
    company = Company.objects.get(user=user)

    vacancy = [i.id for i in Vacancy.objects.filter(companies=company)]
    applyjob = Applyjob.objects.filter(vacancy__in=vacancy, Status="Sorted")
    return render(request, 'employee/sortListedApplication.html', locals())


def rejectApplication(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = request.user
    company = Company.objects.get(user=user)

    vacancy = [i.id for i in Vacancy.objects.filter(companies=company)]
    applyjob = Applyjob.objects.filter(vacancy__in=vacancy, Status="Rejected")

    return render(request, 'employee/rejectApplication.html', locals())


def allApplication(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = request.user
    company = Company.objects.get(user=user)
    vacancies = Vacancy.objects.filter(companies=company)
    vacancy = [i.id for i in vacancies]
    jobs = list(set([i.JobTitle.strip().lower().title() for i in vacancies]))
    applyjob = Applyjob.objects.filter(vacancy__in=vacancy)

    if request.method == "POST":
        job = request.POST['jobs']
        # List of resume URLs
        applyjobs = Applyjob.objects.filter(vacancy__JobTitle=job, Recommanded=True)
        if applyjobs.count() > 0:
            scheme = request.scheme
            host = request.META['HTTP_HOST']
            base_url = '{}://{}'.format(scheme, host)

            # Create an in-memory byte stream
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for url in applyjobs:
                    # Fetch the file from the URL
                    response = requests.get(f"{base_url}{url.Resume.url}")
                    # Extract the filename from the URL
                    filename = url.candidate.user.first_name + " " + url.candidate.user.last_name + " " + \
                               url.Resume.url.split('/')[-1]

                    # Add the file to the zip archive
                    zip_file.writestr(filename, response.content)

            # Seek to the beginning of the buffer
            zip_buffer.seek(0)

            # Create a response with the zip file
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="resumes.zip"'

            return response
        else:
            error = "yes"
        return render(request, 'employee/allApplication.html', locals())

    else:
        return render(request, 'employee/allApplication.html', locals())


def viewAppliedApplication(request, pid):
    if not request.user.is_authenticated:
        return redirect('employees')
    applyjob = Applyjob.objects.get(id=pid)

    message = Message.objects.filter(appjob=applyjob)
    applyjobid = applyjob.id
    msgcount = Message.objects.filter(appjob=applyjob).count()

    if request.method == "POST":
        Messages = request.POST['Messages']
        Status = request.POST['Status']

        try:
            msg = Message.objects.create(appjob=applyjob, Messages=Messages, Status=Status)
            applyjob.Message = Messages
            applyjob.Status = Status
            applyjob.save()
            error = "no"
        except:
            error = "no"
    return render(request, 'employee/viewAppliedApplication.html', locals())


def download_resumes(request, job):
    # List of resume URLs
    applyjobs = Applyjob.objects.filter(vacancy__JobTitle=job, Recommanded=True)
    scheme = request.scheme
    host = request.META['HTTP_HOST']
    base_url = '{}://{}'.format(scheme, host)

    # Create an in-memory byte stream
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for url in applyjobs:
            # Fetch the file from the URL
            response = requests.get(f"{base_url}{url.Resume.url}")
            # Extract the filename from the URL
            filename = url.candidate.user.first_name + " " + url.candidate.user.last_name + " " + \
                       url.Resume.url.split('/')[-1]

            # Add the file to the zip archive
            zip_file.writestr(filename, response.content)

    # Seek to the beginning of the buffer
    zip_buffer.seek(0)

    # Create a response with the zip file
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="resumes.zip"'

    return response


def viewstudentEduDtls(request, pid):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = User.objects.get(id=pid)
    education = Education.objects.get(user=user)
    return render(request, 'employee/viewstudentEduDtls.html', locals())


def vacancyReport(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = request.user
    company = Company.objects.get(user=user)

    if request.method == "POST":
        fd = request.POST['FromDate']
        td = request.POST['ToDate']

        vacancy = Vacancy.objects.filter(Q(JobpostingDate__gte=fd) & Q(JobpostingDate__lte=td), companies=company)
        return render(request, 'employee/vacancyReportDtls.html', locals())
    return render(request, 'employee/vacancyReport.html', locals())


def applicationCountReport(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    user = request.user
    company = Company.objects.get(user=user)

    if request.method == "POST":
        fd = request.POST['FromDate']
        td = request.POST['ToDate']

        applyjob = Applyjob.objects.filter(Q(ApplyDate__gte=fd) & Q(ApplyDate__lte=td),
                                           vacancy__in=Vacancy.objects.filter(companies=company))

        return render(request, 'employee/applicationCountReportDtls.html', locals())
    return render(request, 'employee/applicationCountReport.html', locals())


def employerChangePwd(request):
    if not request.user.is_authenticated:
        return redirect('employees')
    error = ""
    user = request.user
    if request.method == "POST":
        o = request.POST['oldpassword']
        n = request.POST['newpassword']
        try:
            u = User.objects.get(id=request.user.id)
            if user.check_password(o):
                u.set_password(n)
                u.save()
                error = "no"
            else:
                error = 'not'
        except:
            error = "yes"
    return render(request, 'employee/employerChangePwd.html', locals())


# ============================  Admin Here  ===========================

def admin_login(request):
    error = ""
    if request.method == 'POST':
        u = request.POST['uname']
        p = request.POST['pwd']
        user = authenticate(username=u, password=p)
        try:
            if user.is_staff:
                login(request, user)
                error = "no"
            else:
                error = "yes"
        except:
            error = "yes"
    return render(request, 'admin_login.html', locals())


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    totalcompany = Company.objects.filter(Approved='True').count()
    totalApprovals = Company.objects.filter(Approved='False').count()
    totalcandidate = Candidate.objects.all().count()
    totalvacancy = Vacancy.objects.all().count()

    return render(request, 'admin/dashboard.html', locals())


def totalRegCompany(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    company = Company.objects.filter(Approved='True')
    approvals = Company.objects.filter(Approved='False')
    return render(request, 'admin/totalRegCompany.html', locals())


def viewCompanyDtls(request, pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    company = Company.objects.get(id=pid)
    return render(request, 'admin/viewCompanyDtls.html', locals())


def approveCompany(request, pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    comp = Company.objects.get(id=pid)
    comp.Approved = 'True'
    comp.save()
    return redirect('totalRegCompany')


def rejectCompany(request, pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    comp = Company.objects.get(id=pid)
    comp.delete()
    return redirect('totalRegCompany')


def totalRegStudent(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    candidate = Candidate.objects.all()
    return render(request, 'admin/totalRegStudent.html', locals())


def viewStudentDtls(request, pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    candidate = Candidate.objects.get(id=pid)
    return render(request, 'admin/viewStudentDtls.html', locals())


def totalVacancy(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    vacancy = Vacancy.objects.all()
    return render(request, 'admin/totalVacancy.html', locals())


def viewVacancyDtls(request, pid):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    vacancy = Vacancy.objects.get(id=pid)
    return render(request, 'admin/viewVacancyDtls.html', locals())


def bwdateComReg(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    if request.method == "POST":
        fd = request.POST['FromDate']
        td = request.POST['ToDate']
        company = Company.objects.filter(Q(CompanyRegdate__gte=fd) & Q(CompanyRegdate__lte=td))
        return render(request, 'admin/companydatesReportsDetails.html', locals())
    return render(request, 'admin/bwdateComReg.html', locals())


def admvacancyReport(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    if request.method == "POST":
        fd = request.POST['FromDate']
        td = request.POST['ToDate']

        company = Company.objects.filter(Q(CompanyRegdate__gte=fd) & Q(CompanyRegdate__lte=td))
        return render(request, 'admin/admvacancyReportDtls.html', locals())
    return render(request, 'admin/admvacancyReport.html', locals())


def adminChangePwd(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    error = ""
    user = request.user
    if request.method == "POST":
        o = request.POST['oldpassword']
        n = request.POST['newpassword']
        try:
            u = User.objects.get(id=request.user.id)
            if user.check_password(o):
                u.set_password(n)
                u.save()
                error = "no"
            else:
                error = 'not'
        except:
            error = "yes"
    return render(request, 'admin/adminChangePwd.html', locals())


def Logout(request):
    logout(request)
    return redirect('index')
