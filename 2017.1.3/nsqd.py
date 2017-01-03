import os
import sys
import time
import subprocess
import json
import random

while(1):
	time.sleep(2)
	ID = random.randint(0,999999)
	msg = {"ID":ID,"Command":"sh init.sh --type=2C4G","Args":"[a,b,c]","IsExit":"Y","source":"http://xxxx:3000/init.sh","filename":"init.sh","path":"/root/monitor/scripts"}	
	ip = 'http://lookupd/put?topic=ip_mysql_request'
	json_msg = json.dumps(msg).encode('utf-8')
	#print json_msg, ip
	
	#create topic
	res2 = 'curl http://lookupd/create_topic?topic=ip_mysql_request'
	#res2 = subprocess.Popen(res2 ,shell=True)
	#create channel
	res1 = 'curl http://lookupd/create_topic?topic=ip_mysql_request\&channel=c'
	#res1 = subprocess.Popen(res1 ,shell=True)
	#put msg
	res = 'curl -d ' + '\''+ json_msg + '\'' +  ' '+ '\''+ ip + '\''
	res = subprocess.Popen(res ,shell=True)
