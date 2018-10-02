#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re

MAIN_LINK = 'https://trashbox.ru/'
API_LINK = '{}ajax.php'.format(MAIN_LINK)
session = requests.Session()

"""
Create 2 files in script directory, 
logins.txt with lines in format login:password 
and comment_ids.txt with lines of comments ids (only numbers)
"""


def get_ajax_code():
	main_html = session.get(MAIN_LINK).text
	ajax_code = re.search("ajax_code = '.+'", main_html)
	if ajax_code is not None:
		print('Login success')
		ajax_code = ajax_code.group(0).split("'")[1]
		return ajax_code
	else:
		print('Login error')
		return None


def auth(login, password):
	session.cookies.clear()
	auth_data = {
		'login': login,
		'pass': password,
		'remember': '1',
		't_control': '1'
	}
	session.post(API_LINK, data=auth_data)
	return get_ajax_code()


def vote_comment(ajax_code, comment_id, upvote=False):
	vote_data = dict(
		mycat='234',
		type='1',
		action='vote',
		vote='-1' if not upvote else '+1',
		id=comment_id,
		t_control='1',
		ajax_code=ajax_code
	)

	vote_request = session.post(API_LINK, data=vote_data)
	me_data = re.search('(new user) (.+)', vote_request.text).group(2).split(', ')
	account_name = me_data[2]
	if me_data[1] == '1':
		print('Account', account_name, 'is blocked')
		return False
	else:
		print('Account', account_name, 'is not blocked')

	free_votes = int(float(me_data[13]) // 0.3)  # some black magic
	print('Account', account_name, 'can put ', free_votes, 'votes')
	if free_votes < 1:
		print('No free votes')
		return False
	else:
		return True


def voter():
	db_path = 'logins.txt'
	with open(db_path, 'r') as users:
		user_data = users.readlines()

	for user in user_data:
		user_auth_info = user.split(":")
		if len(user_auth_info) != 2:  # if string is invalid
			print('Invalid login line', user)
			continue

		login, password = user_auth_info
		login.strip()
		password.strip()

		ajax_code = auth(login, password)
		if ajax_code is None:
			print('Invalid account', login)
			continue

		with open('comment_ids.txt', 'r') as comment_ids:
			for comment_id in comment_ids.readlines():
				if vote_comment(ajax_code, comment_id):
					print('Voted for comment', comment_id.strip(), 'successfully')
				else:
					print('Going to next account')
					break


if __name__ == '__main__':
	voter()
