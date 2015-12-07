#!/usr/bin/env python3
# Translate Chinese numeral into the intermediate number representation:
#     <digits>|<powerOfTen>|<unit>
# Three variants (differ in the way large numbers are handled):
#   1. CAT: Change at tens (1 Yi = 10 Wan, 1 Zhao = 10 Yi, etc.)
#   2. CAM: Change at myriads (1 Yi = 10000 Wan, 1 Zhao = 10000 Yi, etc.)
#   3. CAX: Change at exhaustion (1 Yi = 1 Wan^2, 1 Zhao = 1 Yi^2, etc.)
# Default behavior is CAM.
# If the number string doesn't fit CAM, then attempt digit-by-digit translation (require all the characters to be digit characters);
# If that doesn't fit, then attempt CAT;
# If that doesn't fit, then attempt CAX;
# If that doesn't fit, then fall back to space-separated character-by-character translation.

import sys
import re
import argparse
from collections import namedtuple

_Record_zh_nn_ = namedtuple("Record_zh_nn", ["value", "type"])

# Read in Chinese number info in "zh.nnn"
numdict = {}
infofile = open("zh.nnn", mode="r")
for line in infofile:
	if line[0] == "#" or line.strip() == "":
		continue
	charName, charValue, charType = line.strip().split("|")
	numdict[charName] = _Record_zh_nn_(value=int(charValue), type=charType.split("-"))
infofile.close()

def value_of(char):
	return numdict[char].value

def is_digit(char):
	if "digit" in numdict[char].type:
		return True
	else:
		return False

def is_zero(char):
	if "zerodigit" in numdict[char].type:
		return True
	else:
		return False

def is_position(char):
	if "position" in numdict[char].type \
		or "largeposition" in numdict[char].type \
		or "smallposition" in numdict[char].type:
		return True
	else:
		return False

def is_largeposition(char):
	if "largeposition" in numdict[char].type:
		return True
	else:
		return False

def is_mixed(char):
	if "mixed" in numdict[char].type:
		return True
	else:
		return False

def all_chars_legal(numstring):
	for char in numstring:
		if char not in numdict:
			return False
	return True

def all_chars_normal(numstring):
	for char in numstring:
		if "normal" not in numdict[char].type:
			return False
	return True

def all_chars_accounting(numstring):
	for char in numstring:
		if "accounting" not in numdict[char].type:
			return False
	return True

def all_chars_digit(numstring):
	for char in numstring:
		if "digit" not in numdict[char].type and "zerodigit" not in numdict[char].type:
			return False
	return True

def translate_digits(numstring):
	out_chars = []
	for char in numstring:
		if is_digit(char) or is_zero(char):
			value = value_of(char)
			out_chars.append(str(value))
	return "".join(out_chars)

def translate_charbychar(numstring):
	out_nums = []
	for char in numstring:
		value = value_of(char)
		if is_digit(char) or is_zero(char) or is_mixed(char):
			out_nums.append(str(value))
		elif is_largeposition(char):
			out_string = "1e{}".format(4 * (value - 3))
			out_nums.append(out_string)
		elif is_position(char):
			if -2 <= value <= 3:
				out_string = str(10 ** value)
			else:
				out_string = "1e{}".format(value)
			out_nums.append(out_string)
		else:
			pass
	return " ".join(out_nums)

def _reduce_to_pattern_(numstring):
	pattern_string = [];
	for char in numstring:
		if "digit" in numdict[char].type:
			pattern = "d";
		elif "zerodigit" in numdict[char].type:
			pattern = "z";
		elif "position" in numdict[char].type:
			pattern = "p"
		elif "largeposition" in numdict[char].type:
			pattern = "l"
		elif "smallposition" in numdict[char].type:
			pattern = "s"
		elif "mixed" in numdict[char].type:
			pattern = "m"
		else:
			pattern = "o"
		pattern_string.append(pattern)
	return "".join(pattern_string)

def fits_cat(numstring,
		allow_zero=True, # Whether allow numstring to consist only of a zero character.
			# Need to set this to False when testing a substring of a bigger number.
		allow_starting_shi=True, # Whether allow numstring to start with Shi (character for "ten").
			# Need to set this to False when testing a non-starting-substring of a bigger number.
		allow_omit_ending_position=True, # Whether allow numstrings such as "Er Bai Wu", "Yi Qian San", etc.
			# Need to set this to False when testing a substring of a bigger number.
		allow_mixed=True, # Whether allow mixed character such as "Nian" (20)
			# Need to set this to False when testing a substring of a bigger number.
		):
	pattern = _reduce_to_pattern_(numstring)
	if not re.search(r"^((d[lp]z?)*d[lp]?|[pm]d?|z)$", pattern):
		return False
	if re.search(r"^z$", pattern) and not allow_zero:
		return False
	if re.search(r"^p", pattern) and not (allow_starting_shi and value_of(numstring[0]) == 1):
		return False
	if re.search(r"pd$", pattern) and (not allow_omit_ending_position) and value_of(numstring[-2]) > 1:
		return False
	if re.search(r"m", pattern) and not allow_mixed:
		return False
	last_pos_val = None
	see_zero = False
	for char in numstring:
		if is_zero(char):
			see_zero = True
		elif is_position(char):
			pos_val = value_of(char)
			if last_pos_val == None \
				or last_pos_val == pos_val + 1 and not see_zero \
				or last_pos_val > pos_val + 1 and see_zero:
				last_pos_val = pos_val
				see_zero = False
			else: # Error: Position characters are out of order, or there's unwanted zero character
				return False
		else: # Only digit characters are possible. Nothing to be checked
			pass
	return True

def translate_cat(numstring):
	total = 0
	digit_stack = []
	position = 0 # The most recent power-of-ten
	see_zero = False
	for char in numstring:
		if is_digit(char):
			digit = value_of(char)
			digit_stack.append(digit)
		elif is_position(char):
			position = value_of(char)
			if len(digit_stack) > 0:
				digit = digit_stack.pop()
			else:
				digit = 1
			total += digit * 10 ** position
			see_zero = False
		elif is_zero(char):
			see_zero = True
		elif is_mixed(char):
			total += value_of(char)
			see_zero = False
		else:
			pass
	if len(digit_stack) > 0: # Handle strings ending with digit characters
		digit = digit_stack.pop()
		if position > 1 and not see_zero: # Handle cases such as "Er Bai Wu, Yi Qian San"
			total += digit * 10 ** (position - 1)
		else: # Handle the normal case
			total += digit
	return total

'''
def fits_cam(numstring):
	recent_chars = []
	last_PoM = float("inf")
	see_zero = False
	
	def _substring_wellformed_():
		substring = "".join(recent_chars)
		if not fits_cat(substring): # Error: The sub-myriad substring is ill-formed
			return False
		nlen = len(str(translate_cat(substring))) # nlen: number of digits of the substring in Arabic numeral form
		if nlen < 4 and not see_zero and last_PoM != float("inf"): # Error: The substring is missing zero characters
			return False
		return True
	
	for char in numstring:
		if is_largeposition(char):
			PoM = value_of(char) - 3 # PoM: power-of-myriad
			if PoM >= last_PoM: # Error: PoM characters are out of order
				return False
			elif PoM < last_PoM - 1 and not see_zero and last_PoM != float("inf"): # Error: Gap not filled by zero characters
				return False
			if not _substring_wellformed_():
				return False
			recent_chars = []
			last_PoM = PoM
			see_zero = False
		elif is_digit(char) or is_position(char):
			recent_chars.append(char)
		elif is_zero(char):
			if len(recent_chars) == 0:
				if see_zero: # Error: Too many zeros
					return False
				see_zero = True
			else:
				recent_chars.append(char)
		else: # Error: See weird character
			return False
	if len(recent_chars) > 0:
		if not _substring_wellformed_():
			return False
	return True
	'''

def _fits_cam_or_cax_(numstring, check_cax=False):
	pattern = _reduce_to_pattern_(numstring)
	re_submyriad = re.compile(r"^pd?|d[pmzd]*|md?") # Regular Expression for sub-myriad substrings
	superpattern = re_submyriad.sub('t', pattern) # Represent sub-myriad substrings with "t" in a "superpattern"
	if not re.search(r"^(t(l+z?t)*l*|z)$", superpattern): # Error: General pattern is not well-formed
		return False
	if not check_cax and re.search(r"ll", superpattern): # Error: CAM doesn't allow consecutive largeposition characters
		return False
	
	# Check the order of largeposition characters (l-chars)
	l_PoMs = [] # power-of-myriad (PoM) values of l-chars
	last_PoM = None
	for char in numstring:
		if is_largeposition(char):
			PoM = value_of(char) - 3
			if last_PoM != None and last_PoM > PoM: # Error: Small l-char immediatedly follows large l-char (for CAX)
				return False
			l_PoMs.append(PoM)
			last_PoM = PoM
		else:
			last_PoM = None
	if check_cax: # CAX: Recursively calculate the true PoM
		for idx, val in enumerate(l_PoMs):
			l_PoMs[idx] = 2 ** (val - 1)
		# nested function definition {
		def _calc_true_PoMs_(start, end):
			if end - start <= 1:
				return
			PoM_max = 0
			idx_max = -1
			for idx in range(start, end):
				PoM = l_PoMs[idx]
				if PoM > PoM_max:
					PoM_max = PoM
					idx_max = idx
			_calc_true_PoMs_(start, idx_max)
			_calc_true_PoMs_(idx_max + 1, end)
			for idx in range(start, idx_max):
				l_PoMs[idx] += PoM_max
		# } nested function definition
		_calc_true_PoMs_(0, len(l_PoMs))
	last_PoM = float("inf")
	for PoM in l_PoMs:
		if PoM >= last_PoM: # Error: l-chars are out of order
			return False
		last_PoM = PoM
	
	# Check all the sub-myriad substrings (t-strings)
	t_strings = []
	submyriad_iter = re_submyriad.finditer(pattern)
	for match in submyriad_iter:
		t_strings.append(numstring[match.start() : match.end()])
	if len(t_strings) == 1:
		if not fits_cat(t_strings[0]):
			return False
	elif len(t_strings) > 1:
		if not fits_cat(t_strings[0], allow_zero=False, 
				allow_omit_ending_position=False, allow_mixed=False):
			return False
		for idx in range(1, len(t_strings)):
			if not fits_cat(t_strings[idx], allow_zero=False, allow_starting_shi=False, 
				allow_omit_ending_position=False, allow_mixed=False):
				return False
	else: # len(t_strings) == 0
		pass
	
	# Check zero characters
	l_ptr = 0
	t_ptr = 0
	see_z = False
	need_z = False
	last_PoM = None
	for idx, symbol in enumerate(superpattern):
		if symbol == "z":
			see_z = True
		elif symbol == "l":
			PoM = l_PoMs[l_ptr]
			if l_ptr > 0: # Do nothing for the first l-char
				if superpattern[idx - 1] != "l": # Previous symbol in superpattern is not "l"
					if last_PoM > PoM + 1:
						need_z = True
					if (need_z and not see_z) or (not need_z and see_z): # Error: Missing or excessive zero character
						return False
				else: # Consecutive l-chars: skip later PoMs (only for CAX)
					pass
			see_z = False
			need_z = False
			last_PoM = PoM
			l_ptr += 1
		elif symbol == "t":
			if t_ptr > 0: # Do nothing for the first t-string
				t_str = t_strings[t_ptr]
				order = len(str(translate_cat(t_str)))
				if order < 4:
					need_z = True
			t_ptr += 1
		else:
			return False # Should not be here
	if superpattern[-1] == "t":
		if last_PoM != None and last_PoM > 1:
			need_z = True
		if (need_z and not see_z) or (not need_z and see_z):
			return False
	
	return True

def fits_cam(numstring):
	return _fits_cam_or_cax_(numstring, check_cax=False)

def fits_cax(numstring):
	return _fits_cam_or_cax_(numstring, check_cax=True)

def translate_cam(numstring):
	total = 0
	recent_chars = []
	for char in numstring:
		if is_largeposition(char):
			PoM = value_of(char) - 3 # PoM: power-of-myriad
			subtotal = translate_cat("".join(recent_chars))
			total += subtotal * 10000 ** PoM
			recent_chars = []
		elif is_digit(char) or is_position(char) or is_mixed(char):
			recent_chars.append(char)
		else:
			pass
	if len(recent_chars) > 0:
		subtotal = translate_cat("".join(recent_chars))
		total += subtotal
	return total

def translate_cax(numstring):
	val_LLP = 0 # the value of the "LLP": largest-"largeposition"-number
	idx_LLP = -1 # the character position of the LLP
	for idx, char in enumerate(numstring):
		if is_largeposition(char):
			val = value_of(char)
			if val > val_LLP:
				val_LLP = val
				idx_LLP = idx
	if val_LLP == 0: # No largeposition number in numstring
		return translate_cat(numstring)
	else:
		big_subtotal = translate_cax(numstring[:idx_LLP])
		small_subtotal = translate_cax(numstring[idx_LLP+1:])
		multiplier = 10 ** (2 ** (val_LLP - 2))
		total = big_subtotal * multiplier + small_subtotal
		return total

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	arggroup_mode = parser.add_mutually_exclusive_group()
	arggroup_mode.add_argument("-c", "--charbychar", dest="mode", action="store_const", const="charbychar",
		help = "character-by-character translation")
	arggroup_mode.add_argument("-d", "--digits", dest="mode", action="store_const", const="digits",
		help = "concatenated digit translation")
	arggroup_mode.add_argument("-t", "--cat", dest="mode", action="store_const", const="cat",
		help = "change-at-tens translation")
	arggroup_mode.add_argument("-m", "--cam", dest="mode", action="store_const", const="cam",
		help = "change-at-myriads translation")
	arggroup_mode.add_argument("-x", "--cax", dest="mode", action="store_const", const="cax",
		help = "change-at-exhaustion translation")
	arggroup_mode.add_argument("-a", "--all", dest="mode", action="store_const", const="all",
		help = "show all kinds of possible translations")
	args = parser.parse_args()
	
	if args.mode == None:
		for line in sys.stdin:
			numstring = line.strip()
			if not all_chars_legal(numstring):
				answer = numstring
			elif fits_cam(numstring):
				answer = translate_cam(numstring)
			elif all_chars_digit(numstring):
				answer = translate_digits(numstring)
			elif fits_cat(numstring):
				answer = translate_cat(numstring)
			elif fits_cax(numstring):
				answer = translate_cax(numstring)
			else:
				answer = translate_charbychar(numstring)
			print(answer)
	elif args.mode in ["charbychar", "digits", "cat", "cam", "cax"]:
		for line in sys.stdin:
			numstring = line.strip()
			if not all_chars_legal(numstring):
				answer = numstring
			else:
				translate = eval("translate_{}".format(args.mode))
				answer = translate(numstring)
			print(answer)
	elif args.mode == "all":
		for line in sys.stdin:
			numstring = line.strip()
			print(numstring)
			if not all_chars_legal(numstring):
				print("  Illegal")
			else:
				if not all_chars_normal(numstring):
					print("  Not all characters are normal")
				if all_chars_accounting(numstring):
					print("  All characters are for accounting")
				print(" pattern:", _reduce_to_pattern_(numstring))
				print("   chars:", translate_charbychar(numstring))
				if all_chars_digit(numstring):
					print("* ", end="")
				else:
					print("  ", end="")
				print("digits:", translate_digits(numstring))
				if fits_cat(numstring):
					print("* ", end="")
				else:
					print("  ", end="")
				print("   CAT:", translate_cat(numstring))
				if fits_cam(numstring):
					print("* ", end="")
				else:
					print("  ", end="")
				print("   CAM:", translate_cam(numstring))
				if fits_cax(numstring):
					print("* ", end="")
				else:
					print("  ", end="")
				print("   CAX:", translate_cax(numstring))
	else:
		print("Error in {}: Unkown mode '{}'".format(sys.argv[0], args.mode))
