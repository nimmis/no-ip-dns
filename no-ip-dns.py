#!/usr/bin/python
#
# (c) 2013 Kjell haenskold (nimmis) kjell.havneskold@gmail.com
#
# Program to update no-ip.com dynamic DNS addresses 
# throu API
# Version 0.1
#

import argparse
import subprocess
import urllib
import urllib2
import base64

# global variables
Username = "your@user.name" # username at no-ip.com
Password = "password" # password at no-ip.com
sendip   = "" # ip to send to no-ip.com, blank to use router IP
updateip = "" # ip for update
version  = 0.1

checkipurl = "http://checkip.dyndns.org" # url to get global ip
check_pre  = "IP Address: " # pre split
check_post = "</body>" # post plit
digcmd    = "/usr/bin/dig"

# command line options
parser = argparse.ArgumentParser()
parser.add_argument('--force', action='store_true', help='Force update of IP')
parser.add_argument('--dryrun', action='store_true', help='Do all without sending')
parser.add_argument('--setip', help='define ip to set')
parser.add_argument('--info', action='store_true', help='show info')
parser.add_argument('hostname',metavar='hostname')
args = parser.parse_args()

# get known ip from dns
def get_known_ip():
	try:
		ip=subprocess.check_output([digcmd,"+short",args.hostname])
		return ip.rstrip()
	except OSError, e:
		print "OS Error in dig :"+e.strerror
		quit()


# determine current ip
def get_current_ip():
	ret_data = urllib.urlopen(checkipurl)
	ret_str = ret_data.read()
	parts = ret_str.split(check_pre)
	ip = parts[1].split(check_post)
	return ip[0]

def update_noip():

	extra_get = urllib.urlencode({'hostname' : args.hostname, 'myip' : update_ip})
	request = urllib2.Request("http://dynupdate.no-ip.com/nic/update?",extra_get)
	request.add_header("User-Agent",'Nimmis Raspbery Pi updater/"+version+" kjell.havneskold@gmail.com')
	base64string = base64.encodestring('%s:%s' % (Username, Password)).replace('\n', '')
	request.add_header("Authorization", "Basic %s" % base64string) 
	try: 
		result = urllib2.urlopen(request)
		print "Result"
		print "Responsd="+result.getcode()
		body = result.read()
		print "body="+body
		# interpret result
		if body.startswith("good"):
			part=body.split(' ')
			print "Update successfull "+args.hostname+" updated to "+part[1]
		elif body.startswith("nochg"):
			part=body.split(' ')
			print "No update "+args.hostname+" already has ip "+part[1]
		elif body=="nohost":
			print args.hostname+"does not exist under specified account."
		elif body=="badauth":
			print "Invalid username password combination."
		elif body=="badagent":
			print "Client disabled. Client should exit and not perform any more updates without user intervention."
		elif body=="!donator":
			print "Feature not available to that particular user such as offline options."
		elif body=="abuse":
			print "Username is blocked due to abuse. Stop sending updates"
		elif body=="911":
			print "Fatal server error, retry no sooner than 30 minutes"
		else:
			print "Unknown response code "+body
	except  IOError, e:
		print "Got an error when trying to connect to no-ip.com"
		print e

known_ip = get_known_ip()

# set update ip to either defined or current
if (args.setip):
	update_ip = args.setip
else:
	update_ip = get_current_ip()

# Determine if ip needs to be updated
needs_update= (known_ip != update_ip) or args.force

if (args.info):
	print "Current IP is "+known_ip
	print "IP to set is  "+update_ip
	if needs_update:
		print "IP should be updated"
	quit()

if needs_update:
	update_noip()
else:
	print "IP is correct, no update needed"

