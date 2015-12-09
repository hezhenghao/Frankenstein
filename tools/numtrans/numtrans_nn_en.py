#!/usr/bin/env python3
# Translate the intermediate number representation to English numeral (standard American English)
# 
# Author：Zhenghao He
import sys
import re
import argparse

# Read in English number info in "en.nnn"
dict_ones = {}
dict_tens = {}
dict_position_normal = {}
dict_position_long = {}
dict_position_indian = {}
dict_ordinal = {}
infofile = open("en.nnn", mode="r")
for line in infofile:
	line = line.strip()
	if line == "" or line[0] == "#":
		continue
	wordName, wordContent, wordTypes = line.split("|")
	wordTypeList = wordTypes.split("-")
	if "ordinal" in wordTypeList:
		dict_ordinal[wordContent] = wordName
	else:
		wordValue = int(wordContent)
		if "zerodigit" in wordTypeList:
			if "normal" in wordTypeList:
				dict_ones[wordValue] = wordName
		elif "digit" in wordTypeList:
			dict_ones[wordValue] = wordName
		elif "10to19" in wordTypeList:
			dict_ones[wordValue] = wordName
		elif "tens" in wordTypeList:
			dict_tens[wordValue] = wordName
		elif "position" in wordTypeList:
			if "normal" in wordTypeList:
				dict_position_normal[wordValue] = wordName
			if "large" in wordTypeList:
				dict_position_long[wordValue * 2 - 6] = wordName
			if "long" in wordTypeList:
				dict_position_long[wordValue] = wordName
			if "indian" in wordTypeList:
				dict_position_indian[wordValue] = wordName
		else:
			pass
infofile.close()
max_position_normal = max(dict_position_normal.keys())
MAX_NORMAL = 10 ** (max_position_normal + 3) - 1
max_position_indian = max(dict_position_indian.keys())
MAX_INDIAN = 10 ** (max_position_indian + 2) - 1

def word_for(number, type="ones", # type is in {ones, tens, position}
		long_scale=False, indian=False):
	if type == "ones":
		return dict_ones.get(number) # dict.get(key) returns None when key is not in dict 
	elif type == "tens":
		return dict_tens.get(number)
	elif type == "position":
		if indian and number in dict_position_indian:
			return dict_position_indian[number] # dict[key] raises error when key is not in dict
		if long_scale and number in dict_position_long:
			return dict_position_long[number]
		return dict_position_normal.get(number)
	else:
		return None

def ordinal_of(cardinal):
	match_last_word = re.search(r"\w+$", cardinal)
	last_word = cardinal[match_last_word.start():]
	if last_word in dict_ordinal:
		ordinal_last_word = dict_ordinal[last_word]
	else:
		ordinal_last_word = last_word + "th"
	ordinal = cardinal[:match_last_word.start()] + ordinal_last_word
	return ordinal

# TODO: ordinal with digits, eg. 15th, 21st, 202nd, etc

def translate_xx(number):
	if 0 <= number <= 19:
		answer = word_for(number)
	else:
		tens, ones = divmod(number, 10)
		word_tens = word_for(tens, type="tens")
		if word_tens == None:
			answer = None
		else:
			if ones > 0:
				answer = word_tens + "-" + word_for(ones)
			else:
				answer = word_tens
	return answer

def translate_xxxx(number, use_and=False, use_hundred=True):
	if 0 <= number <= 99:
		answer = translate_xx(number)
	elif 100 <= number <= 9999:
		hundreds, subhundred = divmod(number, 100)
		str_hundreds = translate_xx(hundreds)
		if subhundred > 0:
			str_subhundred = translate_xx(subhundred)
			if use_hundred:
				str_link = " hundred "
				if use_and:
					str_link += "and "
			else:
				if subhundred >= 10:
					str_link = "-"
				else:
					str_link = "-oh-"
			answer = str_hundreds + str_link + str_subhundred 
		else:
			answer = str_hundreds + " hundred"
	else:
		answer = None
	return answer

def translate(number, long_scale=False, indian=False, use_and=False, use_hundred=True):
	if indian and number > MAX_INDIAN:
		return None
	if not indian and number > MAX_NORMAL:
		return None
	if number <= 999:
		answer = translate_xxxx(number, use_and, use_hundred)
	else:
		head_chunk, tail_chunk = divmod(number, 1000)
		answer = ""
		if tail_chunk > 0:
			answer = translate_xxxx(tail_chunk, use_and, use_hundred)
		position = 3
		if indian:
			position_increment = 2
		else:
			position_increment = 3
		while head_chunk > 0:
			head_chunk, tail_chunk = divmod(head_chunk, 10 ** position_increment)
			if tail_chunk > 0:
				word_chunk = translate_xxxx(tail_chunk, use_and, use_hundred)
				word_position = word_for(position, type="position", long_scale=long_scale, indian=indian)
				answer = word_chunk + " " + word_position + " " + answer
				answer = answer.strip() # In case that in the previous statement, 'answer' on the RHS is empty
			position += position_increment
	return answer

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--ordinal", action="store_true",
		help = "ordinal number translation")
	parser.add_argument("-l", "--long_scale", action="store_true",
		help = "interpret large numbers with long scale")
	parser.add_argument("-i", "--indian", action="store_true",
		help = "use Indian English words for large numbers")
	parser.add_argument("-n", "--use_and", action="store_true",
		help = "use 'and' in translation")
	parser.add_argument("-H", "--no_hundred", dest="use_hundred", action="store_false",
		help = "don't use 'hundred' when tens and ones are not all zero")
	parser.add_argument("-a", "--all", action="store_true",
		help = "show all kinds of possible translations")
	args = parser.parse_args()
	
	if args.all:
		print("dict_ones =", dict_ones)
		print("dict_tens =", dict_tens)
		print("dict_position_normal =", dict_position_normal)
		print("dict_position_long =", dict_position_long)
		print("dict_position_indian =", dict_position_indian)
		print("dict_ordinal =", dict_ordinal)
		for line in sys.stdin:
			number = int(line.strip())
			print(number)
			print("  Word:", word_for(number))
			print("  Translate XX:", translate_xx(number))
			print("  Translate XXXX:", translate_xxxx(number))
			print("  Normal:", translate(number))
			print("  Ordinal:", translate(number, ordinal=True))
			print("  Long scale:", translate(number, long_scale=True))
			print("  Indian:", translate(number, indian=True))
			print("  Use 'and':", translate(number, use_and=True))
			print("  Don't use 'hundred':", translate(number, use_hundred=False))
	else:
		for line in sys.stdin:
			number = int(line.strip())
			answer = translate(number, 
					long_scale=args.long_scale, 
					indian=args.indian, 
					use_and=args.use_and, 
					use_hundred=args.use_hundred)
			if args.ordinal:
				answer = ordinal_of(answer)
			print(answer)
