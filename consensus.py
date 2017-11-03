import time
import datetime
from ethapi import *

IPv4_PREFIX_LENGTH = 32
IPv6_PREFIX_LENGTH = 128

def get_hash_from_json_block(json_block):
	return json_block['result']['hash']

def get_current_timestamp():
	curDate = time.strftime("%x")
	curTime = time.strftime("%X")
	now = curDate+" "+curTime
	return time.mktime(datetime.datetime.strptime(now, "%m/%d/%y %H:%M:%S").timetuple())

def get_random_hash():
	# Get Ethereum hash
	last_block_number = get_last_block_number()
	json_block = get_block_by_number(last_block_number)
	eth_hash = get_hash_from_json_block(json_block)
	eth_hash_bits = from_hex_to_bits(eth_hash,256)

	# Get Nist hash
	timestamp = get_current_timestamp()
	nist_hash = get_hash_from_NIST(int(timestamp))
	nist_hash = hex(int(nist_hash.replace('L', '').zfill(8), 16))[:-1]
	nist_hash_bits = from_hex_to_bits(nist_hash,512)

	xor = long(eth_hash_bits,2)^long(nist_hash_bits,2)
	return from_long_to_bits(xor)

def from_hex_to_bits(h,nbits):
	return bin(int(h,16))[2:].zfill(nbits)

def from_long_to_bits(l):
	res = "{0:b}".format(l)
	while len(res) < 512:
		res = "0"+res
	return res

def which_protocol():
	if 0:
		return "IPv6"
	else:
		return "IPv4"

def consensus_for_IPv6(hash):
	ngroup = len(hash)/IPv6_PREFIX_LENGTH
	address = []
	for i in range (0,len(hash),IPv6_PREFIX_LENGTH):
		ini_xor = int(hash[i],2)
		for j in range (i+1,i+IPv6_PREFIX_LENGTH):
			ini_xor = ini_xor^int(hash[j],2)
		address.append(ini_xor)

	return address

def consensus_for_IPv4(hash):
	ngroup = len(hash)/IPv4_PREFIX_LENGTH
	address = []
	for i in range (0,len(hash),IPv4_PREFIX_LENGTH):
		ini_xor = int(hash[i],2)
		for j in range (i+1,i+IPv4_PREFIX_LENGTH):
			ini_xor = ini_xor^int(hash[j],2)
		address.append(ini_xor)

	return address

def who_signs():
	protocol = which_protocol()
	hash = get_random_hash()
	if protocol == "IPv6":
		return consensus_for_IPv6(hash)
	else:
		return consensus_for_IPv4(hash)

print (who_signs())