import random as rd

from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password,
)
from django.utils.crypto import get_random_string
import hashlib, uuid

def make_random_password(length=10,                              allowed_chars='abcdefghijkmnpqrstuvwxyz                            ABCDEFGHIJKLMNPQRSTUVWXYZ                                           123456789'):
    return get_random_string(length, allowed_chars)

def resize(i):
    s = str(i)
    if len(s) == 1:
        return "0" + s
    return s

def make_random_datetime(year_min, year_max, time = False):
    year = str(rd.randint(year_min, year_max))
    month = resize(rd.randint(1,12))
    day = resize(rd.randint(1,28))
    if time:
        hour = resize(rd.randint(0,23))
        minute = resize(rd.randint(0,59))
        second = resize(rd.randint(0,59))
        return year + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + second
    return year + "-" + month + "-" + day

def add_users():
    f = open('BX-CSV-Dump/BX-Users.csv','r', encoding='ISO-8859-1')
    users = f.readlines()
    f.close()

    fnamesfile = open('BX-CSV-Dump/FirstNames.csv','r', encoding='ISO-8859-1')
    fnames = fnamesfile.readlines()
    fnamesfile.close()

    lnamesfile = open('BX-CSV-Dump/LastNames.csv', encoding='ISO-8859-1')
    lnames = lnamesfile.readlines()
    lnamesfile.close()
    try:
        for line in users:
            data = line.replace('|','-').split('";')
            for i in range(len(data)):
                data[i] = data[i][1:]

            raw = make_random_password()
            salt = uuid.uuid4().hex
            password = hashlib.sha256(salt.encode() + raw.encode()).hexdigest() + ':' + salt

            first_name, last_name = rd.choice(fnames)[:-1], rd.choice(lnames)[:-1]
            username = (first_name[:2] + last_name + str(rd.randint(0,10000))).lower()

            hosts = ["@gmail.com", "@laposte.net", "@yahoo.com", "@hotmail.fr", "@outlook.com"]
            email = username + rd.choice(hosts)

            if data[2][0] == "U":
                birthday = make_random_datetime(1950, 2000)
            else:
                age = int(data[2].split('"')[0])
                birthday = make_random_datetime(2017-age,2019-age)

            newline = password + '|' + make_random_datetime(2018,2019,True) + "|false|" + username + "|false|false|" + make_random_datetime(2000,2017,True) + "|" + first_name + "|" + last_name + "|" + data[1] + "|" + email + "|" + birthday + '|' + str(rd.randint(0, 1000)) + "|1|0"
            print(newline)
    except ValueError:
        print(line)
        return 1
    except IndexError:
        print(line)
        return 2

def add_books():
    f = open('BX-Books.csv','r', encoding='ISO-8859-1')
    books = f.readlines()
    f.close()
    try:
        for line in books:
            data = line.replace('|','-').replace('\"','"').replace('"; ','" - ').split('";')
            for i in range(len(data)):
                data[i] = data[i][1:]

            if len(data[0]) < 10:
                data[0] = data[0] + (10-len(data[1]))*"0"
            isbn = data[0][0] + "-" + data[0][1:5] + "-" + data[0][5:9] + "-" + data[0][9]

            if len(data[1]) > 100:
                title = (data[1][:97] + "...").replace("\.", ".")
            else:
                title = data[1]

            price = str(rd.randint(10,500)/10)

            if len(data[2]) > 50:
                author = (data[2][:47] + "...").replace("\.", ".")
            else:
                author = data[2]
            try:
                newline = isbn + "|1|" + title + "|" + price + "|" + str(max(int(data[3]), 2018)) + "|" + data[5] + "|" + str(rd.randint(1,26)) + "|" + author
                print(newline)
            except ValueError:
                pass
    except IndexError:
        print("INDEX ERROR!")
        print(line)
        return 1


def add_ratings():
    f = open('BX-Book-Ratings.csv','r', encoding='ISO-8859-1')
    ratings = f.readlines()
    f.close()
    f = open('BX-Books.csv','r', encoding='ISO-8859-1')
    books = f.readlines()
    f.close()
    ids = []
    for lineb in books:
        data = lineb.replace('|','-').replace('\"','"').replace('"; ','" - ').split('";')
        for i in range(len(data)):
            data[i] = data[i][1:]
        if len(data[0]) == 10:
            isbn = data[0][0] + "-" + data[0][1:5] + "-" + data[0][5:9]
            ids += isbn
    try:
        for line in ratings:
            data = line.replace('|','-').replace('\"','"').replace('"; ','" - ').split('";')
            for i in range(len(data)):
                data[i] = data[i][1:]
            if len(data[1]) == 10:
                isbn = data[1][0] + "-" + data[1][1:5] + "-" + data[1][5:9] + "-" + data[1][9]
            if isbn in ids:
                evaluationInt = int(data[2][:-2])//2
                if evaluationInt > 0 and len(data[0]) > 1:
                    evaluation = str(evaluationInt)
                    newline = make_random_datetime(2000,2019, True) + "|" + evaluation + "|" + isbn + "|" + data[0]
                    print(newline)

    except IndexError:
        print("INDEX ERROR!")
        print(line)
        return 1

add_users()
