#/usr/bin/env python
#coding: utf-8
#Version: db:1.1.1

import os,sys,json
import nsq
import commands
import re
import tornado.ioloop
import time
import threading
import Queue
import subprocess
import urllib2,urllib
from multiprocessing import Process

global readQueue
global writeQueue

readQueue = Queue.Queue(0) #block Queue
writeQueue = Queue.Queue(0)


class Reader(threading.Thread):

	def __init__(self, t_name, queue, addr='xxxx', topic="a", channel="c",lookupd_poll_interval=5,max_in_flight=1):
		threading.Thread.__init__(self,name=t_name)
		self.addr = addr
		self.topic = topic
		self.channel = channel
		self.lookupd_poll_interval = lookupd_poll_interval
		self.max_in_flight = max_in_flight
		self.buf = []
		self.reader = nsq.Reader(message_handler=self.writeQ, 
							lookupd_http_addresses=[self.addr],lookupd_poll_interval=self.lookupd_poll_interval,
							topic=self.topic, channel=self.channel, max_in_flight=self.max_in_flight)
		self.data = queue

	def writeQ(self, message):
		global writeQueue
		try:
			self.data.put(message) # put message from nsq to block queue
		except Exception,e:	
			pass
		return True

	def run(self):
		pass


class Writer(threading.Thread):

	def __init__(self, t_name, queue, addr='xxxx' ,topic="Mysql_Monitor"):
		threading.Thread.__init__(self,name=t_name)
		self.data = queue
		self.addr = addr
		self.topic = topic
		try:
			self.writer = nsq.Writer(nsqd_tcp_addresses=[self.addr])
		except Exception,e:
			pass		

	def pub_message(self):
		try:
			self.writer.pub(self.topic, self.data.get(1), self.finish_pub)
		except Exception,e:
			pass

	def finish_pub(self, conn, res):
		pass

	def run(self):
		while(1):
			self.pub_message()
			time.sleep(1)


class Execute(threading.Thread):

	def __init__(self, t_name, queue):
		threading.Thread.__init__(self, name = t_name)
		self.data = queue

	# download callback
	def reporthook(self, block_read, block_size, total_size):
		if not block_read:
			res = "connection opened"
			return
		if total_size<0:
			#print "read %d blocks (%dbytes)" %(block_read,block_read*block_size)
			res = 'read ' + str(block_read) + ' blocks (' + str(block_read*block_size) + 'bytes)'
		else:
			amount_read=block_read*block_size;
			#print 'Read %d blocks,or %d/%d' %(block_read,block_read*block_size,total_size)
			res = 'Read ' + str(block_read) + ' blocks,or ' + str(block_read*block_size) + '*' + str(total_size)
		return

	# download scripts
	def _download(self, RES):
		try:
			des = RES['path']+'/'+RES['filename']
			msg = urllib.urlretrieve(RES['source'], des, reporthook = self.reporthook)
		except Exception, e:
			pass
		sys.stdout.flush()
		return True

	def strify(self, sessionId, result):
		res = {}
		res['ID'] = sessionId
		if result[0] == '{':
			Res = json.loads(result)
			res['result'] = Res
		else:
			res['result'] = result
		RES = json.dumps(res, indent=4).encode("utf-8")
		return RES

	def _exec(self, RES):
		path = 'cd '+ RES['path'] + ' && '+ RES['Command']
		try:
			global writeQueue
			res = subprocess.Popen(path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			while True:
				line = res.stdout.readline()
				line = self.strify(RES['ID'], line)
				writeQueue.put(line)
				if subprocess.Popen.poll(res)==0:
					break

		except Exception,e:
			return e

	def run(self):
		while(1):
			global writeQueue
			tmp = self.data.get(1).body
			try:
				RES = json.loads(tmp)
			except Exception,e:
				print e
			des = RES['path']+'/'+RES['filename']
			if os.path.exists(RES['path']):
				if os.path.exists(des):
					retcode = self._exec(RES)
				else: 
					self._download(RES)
					retcode = self._exec(RES)
			else:
				res = self.strify(RES['ID'],'dir not exits, try again!')
				writeQueue.put(res)

#multi threads
def foo():
	global readQueue, writeQueue
	try:
		lookupd_address = os.getenv('lookupd')
		nsqd_address = os.getenv('nsqd')
		nsqd_address = nsqd_address.split(',')

		request_topic = os.getenv('sub_topic')
		response_topic = 'mysql_response'

		# create subtopic & channel
		subtopic = "curl http://"+lookupd_address+"/create_topic?topic="+request_topic
		subchannel = "curl http://"+lookupd_address+"/create_channel?topic="+request_topic+"\&channel=c"
		(status,res) = commands.getstatusoutput(subtopic)
		(status1,res1) = commands.getstatusoutput(subchannel)

		if lookupd_address:
			r = Reader('Reader.', readQueue, lookupd_address, request_topic)
		else:
			r = Reader(t_name = 'Reader.', queue=readQueue)#, topic=request_topic)

		if nsqd_address[0]:
			w = Writer('Writer.', writeQueue, nsqd_address[0], response_topic)
		else:
			w = Writer(t_name='Writer.', queue=writeQueue)#, topic=response_topic)

		e = Execute('Execute.', readQueue)
	except Exception, e:
		pass

	try:
		r.start()
		e.start()
		w.start()
	except Exception,e:
		pass
		#print 'thread start error',e
	nsq.run()
	try:
		r.join()
		e.join()
		w.join()
	except Exception,e:
		pass
		#print 'thread join error',e

#daemon process
def main():
	p = Process(target=foo)
	p.start()
	p.join()

if __name__ == '__main__':
	main()
