import time
import random
import requests
from PIL import Image
import re
import pytesseract
from collections import Counter

"""
Maybe we should use proxies and fake user-agent. Maybe later I will add this. Now better if you use VPN.

"""

session = requests.Session()


def login_generator():
    words_list = ["Here", "You", "Can", "Add", "Some", "Words"]
    first_part = random.choice(words_list)
    second_part = str(random.randint(0, 999))
    third_part = random.choice(words_list)
    login = first_part + second_part + third_part
    password = str(random.randint(11111111, 99999999))
    return [login, password]


def create_new_email():
    API_LINK = 'https://post-shift.ru/api.php'
    new_email_params = {
        'action': 'new',
        'type': 'json'
    }
    new_email_request = session.get(API_LINK, params=new_email_params)
    return new_email_request.json()


def get_first_email(key, delay=15, time_limit=45):
    API_LINK = 'https://post-shift.ru/api.php'
    get_first_email_params = {
        'action': 'getmail',
        'key': key,
        'id': 1,
        'type': 'json',
        'forced': 1
    }
    tries_count = 0
    while True:
        get_first_email_request = session.get(API_LINK, params=get_first_email_params)
        result = get_first_email_request.json()
        drop_email_params = {
            'action': 'delete',
            'key': key,
            'type': 'json'
        }
        if 'error' in result:
            if result['error'] == 'letter_not_found':
                tries_count += 1
                if tries_count >= time_limit // delay:
                    print('[TempMail] Dropping the temp email and exiting from get_first_email().')
                    drop_email_request = session.get(API_LINK, params=drop_email_params)
                    return False
                time.sleep(delay)
                continue
            elif result['error'] == 'key_not_found':
                print('[TempMail] Warning: temp mail key' + key + ' doesn\'t seem to exist. Exiting from get_first_email().')
                return False
            else:
                print('[TempMail] Warning: unexpected error:' + result['error'] + '. Exiting from get_first_email().')
                return False
        drop_email_request = session.get(API_LINK, params=drop_email_params)
        return result['message']


def registration():
    register_data = {
        'login': None,
        'pass': None,
        'pass2': None,
        'mail': None,
        'register_control': None,
        'register': 'Зарегистрироваться'
    }

    mail_data = create_new_email()

    register_page = session.get('https://trashbox.ru/fresh/register/')

    answer_list = []
    for i in range(30):
        captcha_image_bytes = session.get('https://trashbox.ru/register_control.php').content

        with open("captcha.gif", "wb") as captcha:
            captcha.write(captcha_image_bytes)

        im = Image.open('captcha.gif')
        im.save('captcha.png')
        answer = pytesseract.image_to_string(Image.open('captcha.png')).replace(' ', '')
        try:
            answer = int(answer)
            if 1000 <= answer <= 9999:
                answer_list.append(answer)

            else:
                continue
        except ValueError:
            continue

    count = Counter(answer_list)
    max_num = 0
    resolved_captcha = None
    for answer in count.keys():
        if count[answer] > max_num:
            max_num = count[answer]
            resolved_captcha = answer

    auth_data = login_generator()
    register_data['login'] = auth_data[0]
    register_data['pass'] = register_data['pass2'] = auth_data[1]
    register_data['register_control'] = resolved_captcha
    register_data['mail'] = mail_data['email']

    register_post = session.post('https://trashbox.ru/fresh/register/', data=register_data)
    print('Login', register_data['login'], 'sent activation email to', register_data['mail'])
    mail_key = mail_data['key']
    mail_text = get_first_email(key=mail_key)
    if mail_text:
        activation_link = re.search('https:[\/\.\?=&\w]+', mail_text).group(0)
        session.get(activation_link)
        print('Account registered successfully\nLogin: ' + register_data['login'] + '\n' + 'Password: ' + register_data['pass'])
        with open('logins.txt', 'a') as database:
            database.write(register_data['login'] + ':' + register_data['pass'] + '\n')
    else:
        return

while True:
	start_time = time.time()
	registration()
	print("--- %s seconds ---" % (time.time() - start_time))