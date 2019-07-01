#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import ahocorasick
import datetime
import nltk
import re
import time
import zipfile
import os

from sner import Ner
from dateutil.relativedelta import relativedelta
from nltk.corpus import wordnet as wn
from nltk.metrics import jaccard_distance
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams

#For executing commands to the data from the doc and odt
from subprocess import Popen, PIPE

wnl = WordNetLemmatizer()


qualFull  = "./DataBase/QualificationsFull.txt" 
qualAcr = "./DataBase/QualificationsAcr.txt"
skills_path="./DataBase/Skills/Skills.txt"

AhoF = ahocorasick.Automaton()
AhoA = ahocorasick.Automaton()
AhoS = ahocorasick.Automaton()

qualF = dict()
qualA = dict()
skillsAho = []
head = None

index = 0
f = open(qualFull, "r")
for line in f.readlines():
    if line[0:2] == "//":
        head = line[2:-1].lower()
        qualF[head] = []
    else:
        qual = line[:-1].lower()
        qualF[head].append(qual)
        AhoF.add_word(qual, (index, qual))
        index += 1
f.close()

head = None

index = 0
f = open(qualAcr, "r")
for line in f.readlines():
    if line[0:2] == "//":
        head = line[2:-1].lower()
        qualA[head] = []
    else:
        qual = line[:-1]
        qualA[head].append(line[:-1])
        AhoA.add_word(qual, (index, qual))
        index += 1
f.close()

f = open(skills_path, "r")
index = 0
for line in f.readlines():
    skill = line[:-1].lower()
    AhoS.add_word(skill, (index, skill))
f.close()
AhoF.make_automaton()
AhoA.make_automaton()
AhoS.make_automaton()

def convert_pdf_to_txt(file_path):
    
    cmd = ['pdftotext', file_path,'-']
    p = Popen(cmd, stdout=PIPE)
    stdout, stderr = p.communicate()
    string = stdout.decode('ascii', 'ignore')
    
    return string.replace('\n', ' .\n').replace('\t', " . \n")

def convert_doc_to_txt(file_path):
    
    cmd = ['catdoc', file_path]
    p = Popen(cmd, stdout=PIPE)
    stdout, stderr = p.communicate()
    string = stdout.decode('ascii', 'ignore')
    
    return string.replace('\n', ' .\n').replace('\t', " . \n")

"""
def convert_docx_to_txt(path):
    
    document = zipfile.ZipFile(path)
    xml_content = document.read('word/document.xml')
    document.close()
    tree = XML(xml_content)
    
    paragraphs = []
    for paragraph in tree.getiterator(PARA):
        texts = [node.text
                 for node in paragraph.getiterator(TEXT)
                 if node.text]
        if texts:
            paragraphs.append(''.join(texts))

    return '\n\n'.join(paragraphs)
    
"""

def convert_docx_to_txt(file_path):
    
    cmd = ['docx2txt', file_path]
    p = Popen(cmd, stdout=PIPE)
    stdout, stderr = p.communicate()
    string = stdout.decode('ascii', 'ignore')
    
    return string.replace('\n', ' .\n').replace('\t', " . \n")
    

def convert_odt_to_txt(file_path):
    
    cmd = ['odt2txt', file_path]
    p = Popen(cmd, stdout=PIPE)
    stdout, stderr = p.communicate()
    string = stdout.decode('ascii', 'ignore')
    
    return string.replace('\n', " .\n").replace('\t', " . \n")


def document_to_text(file_path):
    
    filename = file_path.split("/")[-1]

    if filename[-4:] == ".doc":
        string = convert_doc_to_txt(file_path)
    elif filename[-5:] == ".docx":
        string = convert_docx_to_txt(file_path)
    elif filename[-4:] == ".odt":
        string = convert_odt_to_txt(file_path)
    elif filename[-4:] == ".pdf":
        string = convert_pdf_to_txt(file_path)
    else:
        raise ValueError("Invalid File Format")
    
    string3 = re.sub("\)"," )",string)
    string2 = re.sub("\(","( ",string3)
    string1 = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', string2)
    clnText = re.sub('\xc2\xa0', ' ', string1)
    cleanText = re.sub('[^\x00-\x7F\n\t]', '', clnText)
    lines = cleanText.split("\n")
    linesText = " . \n".join(lines)
    tabs = linesText.split("\t")
    tabsTe = " . \n".join(tabs)
    tabsText = re.sub("(\s\s)+"," .\n",tabsTe)
    columns = tabsText.split(':')
    columnText = ":.\n".join(columns)
    #EXTRA
    spaces = columnText.split(' ')
    spaceText = " ".join(spaces)
    cleanText = spaceText.replace('|', ' ')
    
    return cleanText


def getPersonNames(string):
    
    
    s = string.replace("\n"," . ")
    tagger = Ner(host='localhost',port=9199)
    taggedEng = tagger.get_entities(s)
    tagger = Ner(host='localhost',port=9198)
    taggedInd = tagger.get_entities(s)
    
    
    
    namesList = []
    name = None
    for word in taggedEng:
        if name != None and word[1] == "PERSON":
            name += " "+str(word[0])
        elif name == None and word[1] == "PERSON":
            name = str(word[0])
        elif name != None:
            namesList.append(name.lower().replace("\n",""))
            name = None
    if name != None:
        namesList.append(name.lower().replace("\n",""))
    
    name = None
    for word in taggedInd:
        if name != None and word[1] == "PERSON":
            name += " "+str(word[0])
        elif name == None and word[1] == "PERSON":
            name = str(word[0])
        elif name != None:
            namesList.append(name.lower().replace("\n",""))
            name = None
    
    if name != None:
        namesList.append(name.lower().replace("\n",""))
    
    n = len(namesList)
    i = 0
    while i < n:
        name = namesList[i]
        j = 0
        while j < n:
            if name in namesList[j] and i != j:
                namesList.pop(i)
                n -= 1
                i -= 1
                break
            j += 1
        i += 1
    
    return namesList
    

def getName(namesList, email):
    
    temp = []
    for name in namesList:
        if str(name).lower() != str(email[0]).lower() and str(name).lower() != str(email[1]).lower():
            temp.append(name)
    namesList = temp
    
    sim = 0.0
    person = None
    for name in namesList:
        simn = 0.0
        division = 0
        for mail in email:
            namemail = mail.split('@')
            namemail = str(namemail[0])
            if mail != None:
                char1_2 = set(ngrams(namemail, 2))
                char1_3 = set(ngrams(namemail, 3))
                char1_4 = set(ngrams(namemail, 4))
                char2_2 = set(ngrams(name, 2))
                char2_3 = set(ngrams(name, 3))
                char2_4 = set(ngrams(name, 4))
                char2_jd = 1.0 - jaccard_distance(char1_2, char2_2)
                char3_jd = 1.0 - jaccard_distance(char1_3, char2_3)
                char4_jd = 1.0 - jaccard_distance(char1_4, char2_4)
                simn += 0.2 * char2_jd + 0.5 * char3_jd + 0.3 * char4_jd
                division += 1
        if division !=  0:
            simn /= division
            if simn > sim:
                sim = simn
                person =  name
        else:
            person = None
            break
    #EXTRA
    if sim < 0.05:
        person = None
    #print sim
    return person


def getEmail(string):
    
    s = string
    regex = re.compile(("([A-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[A-z0-9!#$%&'*+\/=?^_`"
                    "{|}~-]+)*(@|\sat\s)(?:[A-z0-9](?:[A-z0-9-]*[A-z0-9])?(\.|"
                    "\sdot\s))+[A-z0-9](?:[A-z0-9-]*[A-z0-9])?)"))
    
    mails = (email[0] for email in re.findall(regex, s) if not email[0].startswith('//'))
    
    i = 0
    email1 = None
    email2 = None
    for email in mails:
        if i == 0:
            email1 = str(email)
            i += 1
        if i == 1 and str(email) != email1:
            email2 = str(email)
            break
    if not ("@" in str(email1)):
        email1 = str(None)
    if not ("@" in str(email2)):
        email2 = str(None)
    return email1, email2
    

def getMobileNumbers(string):
    
    s = string
    s.encode("utf-8")
    regex = re.compile(r"(\+?(91)?( )*(-)?( )*(0)*((\d{5}( )*(-)?( )*\d{5})|"
                               "(\d{4}( )*(-)?( )*\d{3}( )*(-)?( )*\d{3})|"
                               "(\d{3}( )*(-)?( )*\d{3}( )*(-)?( )*\d{4})|"
                               "(\d{3}( )*(-)?( )*\d{4}( )*(-)?( )*\d{3})))")
    
    mobile_nums = (mn[0] for mn in re.findall(regex, s))
    
    i = 0
    ph_no1 = None
    ph_no2 = None
    for mobile in mobile_nums:
        if i == 0:
            ph_no1 = mobile
        else:
            ph_no2 = mobile
            break
        i += 1
    
    if ph_no1 != None:
        ph_no1.encode("utf-8")
    
    if ph_no2 != None:
        ph_no2.encode("utf-8")
    
    mobile1 = None
    mobile2 = None
    if ph_no1 != None:
        mobile1 = (str(ph_no1).encode("utf-8")).replace("-","").replace(" ","")
        mobile1 = "+91"+mobile1[-10:]
    if ph_no2 != None:
        mobile2 = (str(ph_no2).encode("utf-8")).replace("-","").replace(" ","")
        mobile2 = "+91"+mobile2[-10:]
    
    return [mobile1, mobile2]


def getSkillCount(skills, segment):
    
    skillDict = dict()
    for skill in skills:
        skillDict[skill] = segment.lower().count(skill)
    
    temp = dict()
    for i in list(skillDict):
        temp[i] = 0
    
    for i in skillDict:
        count = 0
        for j in skillDict:
            if i != j and i in j:
                count += skillDict[j]
        temp[i] = skillDict[i] - count
    skillDict = temp
    
    return skillDict
    

def getSkills(s):
    string = re.sub("[\n,]"," . ", s)
    return list(set(getAhoList(AhoS, string, case=False)))
    

def getSegments(string, headings_file_path="./DataBase/Headings.txt"):
    
    hf = open(headings_file_path, "r")
    
    headings = []
    for line in hf.readlines():
        headings.append(line[:-1])
    
    headingList = []
    headingsDefined = set()
    for heading in headings:
        headingList.append(heading.lower())
        headingsDefined.add(heading.lower())
    
    segmentHeadings = ['blank', 'address', 'objective', 'summary', 'education', 'skills', 
                       'academic_projects', 'experience', 'internship', 'achievements', 'misc']
    index = 0
    toggle = False
    classifiedHeadings = dict()
    xi = 0
    for i in range(0, len(headingList)):
        if headingList[i] == "$":
            toggle = True
        if toggle:
            classifiedHeadings[segmentHeadings[index]] = (xi, i)
            xi = i + 1
            index += 1
            toggle = False
        i += 1
    
    fileLines = string.split('\n')
    filteredLines = []
    originalLines = []
    for line in fileLines:
        words = nltk.word_tokenize(line)
        filteredWords = []
        for word in words:
            if (word[0] <= 'z' and word[0] >= 'A') or word[0] == '&':
                filteredWords.append(word.lower())
            elif word == ":":
                break
        originalLines.append(" ".join(words))
        filteredLines.append(" ".join(filteredWords))
    
    segmentHeadings = ['blank', 'address', 'education', 'objective', 'summary', 'skills', 
                       'academic_projects', 'experience', 'internship', 'achievements', 'misc']
    
    segments = dict()
    for seg in segmentHeadings:
        segments[seg] = []
    
    num_lines = len(originalLines)
    i = 0
    blankFlag = True
    while i < num_lines:
        if filteredLines[i] in headingList:
            head = None
            if blankFlag:
                for j in range(0, i):
                    segments['blank'].append(originalLines[j])
                blankFlag = False
            
            index = headingList.index(filteredLines[i])
            if index in range(classifiedHeadings['address'][0], 
                              classifiedHeadings['address'][1]+1):
                head = "address"
            elif index in range(classifiedHeadings['objective'][0], 
                                classifiedHeadings['objective'][1]+1):
                head = "objective"
            elif index in range(classifiedHeadings['summary'][0], 
                                classifiedHeadings['summary'][1]+1):
                head = "summary"
            elif index in range(classifiedHeadings['education'][0], 
                                classifiedHeadings['education'][1]+1):
                head = "education"
            elif index in range(classifiedHeadings['skills'][0], 
                                classifiedHeadings['skills'][1]+1):
                head = "skills"
            elif index in range(classifiedHeadings['academic_projects'][0], 
                                classifiedHeadings['academic_projects'][1]+1):
                head = "academic_projects"
            elif index in range(classifiedHeadings['experience'][0], 
                                classifiedHeadings['experience'][1]+1):
                head = "experience"
            elif index in range(classifiedHeadings['internship'][0], 
                                classifiedHeadings['internship'][1]+1):
                head = "internship"
            elif index in range(classifiedHeadings['achievements'][0], 
                                classifiedHeadings['achievements'][1]+1):
                head = "achievements"
            elif index in range(classifiedHeadings['misc'][0], 
                                classifiedHeadings['misc'][1]+1):
                head = "misc"
            
            i += 1
            while i < num_lines and filteredLines[i] not in headingList:
                segments[head].append(originalLines[i])
                i += 1
        else:
            i += 1
    
    return segments
    

def getAhoList(Aho, segInLine, case=True):
    
    segInLine = segInLine.replace("&", " and ")
    segInLine = segInLine.replace("-", "")
    originalSeg = segInLine
    
    if not case:
        segInLine = segInLine.lower()
    
    quals = []
    for qual in Aho.iter(str(segInLine)):
        start = qual[0] - len(qual[1][1])
        end = qual[0]
        quals.append([start, end, qual[1][1]])
    
    quals.sort(key=lambda x: x[0])
    
    start = None
    end = None
    qualList = []
    if len(quals) > 0:
        start = quals[0][0]
        end = quals[0][1]
    
    lasts = None
    laste = None
    for qual in quals:
        lasts = qual[0]
        laste = qual[1]
        if end >= qual[0]:
            if end < qual[1]:
                if start == qual[0]:
                    end = qual[1]
                else:
                    qualList.append(originalSeg[start+2:end].encode("utf-8"))
                    start = qual[0]
                    end = qual[1]
            else:
                lasts = start
                laste = end
        else:
            qualList.append(originalSeg[start+2:end].encode("utf-8"))
            start = qual[0]
            end = qual[1]
    
    if len(quals) > 0:
        qualList.append(originalSeg[lasts+2:laste].encode("utf-8"))
    
    return qualList
    

def getEducationQualifications(eduSegment):
    
    eduSegmentInLine = segmentInLine(eduSegment)
    
    
    
    qualListF = getAhoList(AhoF, eduSegmentInLine, case=False)
    
    
    qualListA = getAhoList(AhoA, eduSegmentInLine, case=True)
    
    qualList = dict()
    for qual in qualListF:
        for degree in qualF:
            if str(" "+qual.lower()+" ") in qualF[degree]:
                if degree in list(qualList) and len(qualList[degree]) < len(qual):
                    qualList[degree] = qual
                elif degree not in list(qualList):
                    qualList[degree] = qual
    
    for qual in qualListA:
        for degree in qualA:
            if str(" "+qual+" ") in qualA[degree]:
                if degree in list(qualList) and len(qualList[degree]) < len(qual):
                    qualList[degree] = qual
                elif degree not in list(qualList):
                    qualList[degree] = qual
    
    return qualList

    
def refineDates(originalDates):
    
    epoch = datetime.datetime.utcfromtimestamp(0)
    dateList = []
    for y in range(len(originalDates)):
        monthStart = originalDates[y][0]
        yearStart = originalDates[y][1]
        monthEnd = originalDates[y][2]
        yearEnd = originalDates[y][3]

        d1 = datetime.datetime(yearStart, monthStart, 1)
        d2 = datetime.datetime(yearEnd, monthEnd, 1)

        time1 = (d1 - epoch).total_seconds()
        time2 = (d2 - epoch).total_seconds()

        dateList.append([time1, time2])

    

    dateList.sort(key=lambda x: x[0])
    
    start = dateList[0][0]
    end = dateList[0][1]
    requiredTimeList = []
    for i in range(1, len(dateList)):
        if dateList[i][0] < end:
            end = max(end, dateList[i][1])
        else:
            requiredTimeList.append([start, end])
            start = dateList[i][0]
            end = dateList[i][1]

    requiredTimeList.append([start, end])
    
    requiredDateList = []
    for i in range(len(requiredTimeList)):
        requiredDateList.append([datetime.datetime.fromtimestamp(requiredTimeList[i][0]).month, 
                                 datetime.datetime.fromtimestamp(requiredTimeList[i][0]).year, 
                                 datetime.datetime.fromtimestamp(requiredTimeList[i][1]).month, 
                                 datetime.datetime.fromtimestamp(requiredTimeList[i][1]).year])
    
    return requiredDateList
    

def getYears(datesList):
    
    totalExperience = 0.0
    totalYears = 0.0
    totalMonths = 0.0
    now = datetime.date.today()
    months_map = {1: 'Jan', 2: 'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'June', 
                  7:'July', 8:'Aug', 9:'Sept', 10:'Oct', 11:'Nov', 12:'Dec'}
    monthsNum = {'none':0, 'march':3, 'february': 2, 'august': 8, 'april': 4,
                 'june': 6, 'january': 1, 'may': 5, 'november': 11, 'july': 7, 
                 'december': 12, 'september': 9, 'october': 10}
    presentDate = months_map[now.month]+" "+str(now.year)
    nowNum = str(now.year)[-2:]
    regex = re.compile(r"(tillnow|tilldate|till now|till date|currently|current|"
                          "presently|present|till|still working|still)", re.I)
    dates = []
    for date in datesList:
        temp = date
        temp1 = re.sub(regex, presentDate, temp)
        yearDates = re.findall(r"\d+", temp1)
        
        mths = re.findall(r"[A-z]+", temp1)
        if len(mths) > 0:
            months = [mths[0], mths[len(mths) - 1]]
        else:
            months = ['none', 'none']
        if months[1] == 'to':
            months.pop()
        temp = []
        for month in months:
            for key in monthsNum:
                if month.lower() in key:
                    temp.append(monthsNum[key])
                    break
        months = temp
        
        yearStart = None
        yearEnd = None
        if len(yearDates) == 0:
            yearStart = "20"+nowNum
            yearEnd = "20"+nowNum
        elif len(yearDates) == 1:
            mn = yearDates[0]
            start = mn[-2:]
            if start <= nowNum:
                yearStart = "20"+str(start)
                yearEnd = "20"+str(start)
            else:
                yearStart = "19"+str(start)
                yearEnd = "19"+str(start)
        else:
            mn = yearDates[0]
            mx = yearDates[1]
            start = mn[-2:]
            end = mx[-2:]
            if start > nowNum and end > nowNum:
                yearStart = "19"+str(start)
                yearEnd = "19"+str(end)
            elif start > nowNum and end <= nowNum:
                yearStart = "19"+str(start)
                yearEnd = "20"+str(end)
            else:
                yearStart = "20"+str(start)
                yearEnd = "20"+str(end)
        if len(months) == 0:
            monthStart = str(now.month)
            monthEnd = str(now.month)
        elif len(months) == 1:
            monthStart = str(months[0])
            monthEnd = str(months[0])
        else:
            monthStart = str(months[0])
            monthEnd = str(months[1])
        
        yearStart = int(yearStart)
        yearEnd = int(yearEnd)
        monthStart = int(monthStart)
        monthEnd = int(monthEnd)
        if yearStart < 1950 or yearStart > int(now.year):
            continue
        if yearEnd < 1950 or yearEnd > int(now.year):
            continue
        if monthStart == monthEnd and yearStart == yearEnd:
            if monthStart == 0:
                yearEnd += 1
                monthStart = 1
                monthEnd = 1
            elif monthStart == 12:
                monthStart = 11
            else:
                monthEnd += 1
        if monthStart == 0 and monthEnd == 0:
            monthStart = 1
            monthEnd = 1
        
        dates.append([monthStart, yearStart, monthEnd, yearEnd])
        
    refinedDates = refineDates(dates)
    
    yearsList = []
    for date in refinedDates:
        monthStart = date[0]
        yearStart = date[1]
        monthEnd = date[2]
        yearEnd = date[3]
        delta = relativedelta(datetime.date(int(yearEnd), int(monthEnd), 01), datetime.date(int(yearStart), int(monthStart), 01))
        yearsDiff = str(abs(delta.years))+" Year(s)"
        monthsDiff = str(abs(delta.months))+" Month(s)"
        yearsList.append(yearsDiff+", "+monthsDiff)
        totalMonths += abs(delta.months)
        totalYears += abs(delta.years)
    
    totalExperience = round((totalYears+(totalMonths/12.0)), 1)
    
    return totalExperience
    

def segmentInLine(segment):
    
    segInLine = " "
    for line in segment:
        i = 0
        n = len(line)
        while n-i-1 >= 0:
            if line[n-i-1] == ' ' or line[n-i-1] == '.':
                i += 1
            else:
                break
        segInLine += " "+line[:-i]
    segInLine += " "
    
    return segInLine
    

def getExperience(expSegment, summarySegment):
    
    summSegmentInLine = segmentInLine(summarySegment)
    
    regexY =  r"((\d{1,2})(\.)?(\d{1,2})?( )*(\+)?( )*(day's|days|year's|"
    regexY += "month's|years|months|day|weeks|year|month|week))"
    expYears = re.compile(regexY, re.I)
    
    temp = expYears.findall(summSegmentInLine)
    yearsInSumm = 0.0
    regexNum = r"((\d{1,2})(\.\d{1,2})?)"
    
    flagY = True
    flagM = True
    for year in temp:
        y = str(year[0])
        if "year" in y.lower() and flagY:
            yearsInSumm += float(str(re.findall(regexNum, y)[0][0]))
            flagY = False
        elif "month" in y.lower() and flagM:
            yearsInSumm += float(str(re.findall(regexNum, y)[0][0])) / 12.0
            flagM = False
        elif not (flagM and flagY):
            break
    
    if yearsInSumm != 0.0:
        return yearsInSumm
    
    regexD = r"((((Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|"
    regexD += "Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)"
    regexD += "( )*(\')?(\-)?( )*(\d{1,2})?( )*(,)?( )*(\d{2,4})?)|(\d{4}))( )*((-)|(to))?"
    regexD += "( )*((((Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?"
    regexD += "|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)( )*(\')?(\-)?( )*"
    regexD += "(\d{1,2})?( )*(,)?( )*(\d{2,4})?)|(\d{2,4}))|((tillnow|tilldate|till now|"
    regexD += "till date|currently|current|presently|present|till|still working|still))))"
    expDate = re.compile(regexD, re.I)
    
    expSegmentInLine = segmentInLine(expSegment)
    temp = expDate.findall(expSegmentInLine)
    
    dates = []
    for date in temp:
        dates.append(date[0])
    
    totalExp = 0.0
    if len(dates) > 0:
        totalExp = getYears(dates)
    else:
        temp = expYears.findall(expSegmentInLine)
        tempYears = 0.0
        for year in temp:
            y = year[0]
            if "year" in y.lower():
                tempYears = float(str(re.findall(regexNum, y)[0][0]))
                if tempYears > totalExp:
                    totalExp = tempYears
    
    return totalExp
    

def getNameFromSegment(segment, namesList, noise_file):
    
    f = open(noise_file, "r")
    for line in f.readlines():
        segment = segment.replace(line[:-1].lower(), " ")
    f.close()
    
    Aho = ahocorasick.Automaton()
    index = 0
    for name in namesList:
        Aho.add_word(name.lower(), (index, name.lower()))
        index += 1
    
    Aho.make_automaton()
    
    names = []
    for name in Aho.iter(str(segment)):
        start = name[0] - len(name[1][1])
        end = name[0]
        names.append([start, end, name[1][1]])
    
    names.sort(key=lambda x: x[0])
    
    personName = None
    if len(names) > 0:
        personName = names[0][2]
    
    return personName
    

def getFirstNonDictWords(segment):
    
    personName = None
    words = nltk.word_tokenize(segment)
    for word in words:
        temp = None
        if len(wn.synsets(word)) == 0 and len(wn.synsets(wnl.lemmatize(word, 'n'))) == 0:
            temp = word
        if temp != None and personName == None:
            personName = temp
        elif temp != None and personName != None:
            personName += " "+temp
        elif temp == None and personName != None:
            break
    
    return personName


def getDetails(file_path, noise_file="./DataBase/Noise.txt", 
               skills_path="./DataBase/Skills/", 
               qualFull  = "./DataBase/QualificationsFull.txt", 
               qualAcr = "./DataBase/QualificationsAcr.txt"):
    #tstartTime = time.time()
    #startTime = time.time()
    string = document_to_text(file_path)
    #print "doc_to_txt"+str(time.time()-startTime)
    
    #startTime = time.time()
    segments = getSegments(string)
    #print "segments"+str(time.time()-startTime)
    
    #startTime = time.time()
    expSegmentInLine = segmentInLine(segments['experience'])
    #print "expSegLine"+str(time.time()-startTime)
    
    #startTime = time.time()
    intExpSegmentInLine = segmentInLine(segments['internship'])
    #print "intExpSegLine"+str(time.time()-startTime)
    
    #startTime = time.time()
    
    skills = getSkills(string)
    #print "skills"+str(time.time()-startTime)
    
    #startTime = time.time()
    personNamesList = getPersonNames(string)
    name = str(getName(personNamesList, getEmail(string)))
    if name == 'None':
        nameSegInLine = segmentInLine(segments['blank']+segments['address'])
        name = str(getNameFromSegment(nameSegInLine.lower(), personNamesList, noise_file))
        if name == 'None':
            name = getFirstNonDictWords(nameSegInLine.lower())
    #print "Name"+str(time.time()-startTime)
    
    #startTime = time.time()
    email = getEmail(string)
    #print "Email"+str(time.time()-startTime)
    
    #startTime = time.time()
    mobile = getMobileNumbers(string)
    #print "mobile"+str(time.time()-startTime)
    
    #startTime = time.time()
    education = getEducationQualifications(segments['education'])
    #print "education"+str(time.time()-startTime)
    
    #startTime = time.time()
    experience = getExperience(segments['experience'], segments['summary'])
    #print "experience"+str(time.time()-startTime)
    
    #startTime = time.time()
    expSkills = getSkills(expSegmentInLine)
    #print "expSkills"+str(time.time()-startTime)
    
    #startTime = time.time()
    intExperience = getExperience(segments['internship'], [''])
    #print "intExp"+str(time.time()-startTime)
    
    #startTime = time.time()
    intExpSkills = getSkills(intExpSegmentInLine)
    #print "intExpSkills"+str(time.time()-startTime)
    
    #startTime = time.time()
    details = dict()
    details['Name'] = str(name).title()
    details['PrimaryEmail'] = email[0]
    details['SecondaryEmail'] = email[1]
    details['PrimaryMobile'] = mobile[0]
    details['SecondaryMobile'] = mobile[1]
    details['Skills'] = skills
    details['education'] = education
    details['experience'] = experience
    details['expSkills'] = expSkills
    details['internshipExp'] = intExperience
    details['intExpSkills'] = intExpSkills
    
    #print "total"+str(time.time()-tstartTime)
    
    return details
    

def tsvHeadFiller(file_path):
    
    details = getDetails(file_path)
    
    headString = ""
    for detail in details:
        if type(details[detail]) is dict and detail.lower() != "education":
            for innerDetail in details[detail]:
                headString += detail+"_" + innerDetail + "\t"
        elif type(details[detail]) is dict and detail.lower() == "education":
            headString += "Education\t"
        else:
            headString += detail + "\t"
            
    return headString

    
def tsvRowFiller(file_path):
    
    details = getDetails(file_path)
    
    row = ""
    for detail in details:
        if type(details[detail]) is dict and detail.lower() != 'education':
            for innerDetail in details[detail]:
                i = 0
                for item in details[detail][innerDetail]:
                    if i != 0:
                        row += ","+str(item)
                    else:
                        row += str(item)
                        i += 1
                row += "\t"

        elif type(details[detail]) is dict and detail.lower() == "education":
            edu = ""
            i=0
            for innerDetail in details[detail]:
                if i != 0:
                    edu += ","+innerDetail + ":"+str(details[detail][innerDetail])
                else:
                    edu += innerDetail + ":"+str(details[detail][innerDetail])
                    i += 1

            row += str(edu) + "\t"
        else:
            row +=  str(details[detail]) + "\t"
    
    return row
    
def parseZipFiles(zipFolder):
    startTime = time.time()
    zipf  = zipfile.ZipFile(zipFolder)
    
    dpath = './zipfiles/'
    zipf.extractall(dpath)
    fw = open("detailsfromzip.tsv","w")
    fh = open("heads2.tsv","r")
    fw.write(fh.readline())
    fh.close()
    for f in zipf.namelist():
        if "/" not in f:
            fw.write(f+"\t"+tsvRowFiller(dpath+f)+"\n")
    fw.close()
    print time.time() - startTime
def getTime():
    return time.time()
def getExeTime(startTime):
    return time.time() - startTime