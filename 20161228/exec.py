#!/usr/bin/env python
#coding: utf-8

import os,sys,json
import nsq
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

#producer thread
class Reader(threading.Thread):

	def __init__(self, t_name, queue, addr='10.100.188.79:4161', topic="a", channel="c",lookupd_poll_interval=15,max_in_flight=50):
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
			print e
		time.sleep(1)	
		return True
	
	def run(self):
		pass

class Writer(threading.Thread):

	def __init__(self, t_name, queue, addr='10.100.188.79:4150' ,topic="Mysql_Monitor"):
		threading.Thread.__init__(self,name=t_name)
		self.data = queue
		self.addr = addr
		self.topic = topic
		try:
			self.writer = nsq.Writer(nsqd_tcp_addresses=[self.addr])
		except Exception,e:
			print e		

	def pub_message(self):
		try:	
			self.writer.pub(self.topic, self.data.get(1), self.finish_pub)
		except Exception,e:
			print e

	def finish_pub(self, conn, res):
		#print 'Write:' + str(res)
		pass

	def run(self):
		#print 'begin write'
		tornado.ioloop.PeriodicCallback(self.pub_message, 500).start()

class Execute(threading.Thread):

	def __init__(self, t_name, queue):
		threading.Thread.__init__(self, name = t_name)
		self.data = queue

	# download callback
	def reporthook(self, block_read, block_size, total_size):
		global writeQueue
		if not block_read:
			res = "connection opened"
			#writeQueue.put(res)
			return
		if total_size<0:
			#print "read %d blocks (%dbytes)" %(block_read,block_read*block_size)
			res = 'read ' + str(block_read) + ' blocks (' + str(block_read*block_size) + 'bytes)'
			#writeQueue.put(res)
		else:
			amount_read=block_read*block_size;
			#print 'Read %d blocks,or %d/%d' %(block_read,block_read*block_size,total_size)
			res = 'Read ' + str(block_read) + ' blocks,or ' + str(block_read*block_size) + '*' + str(total_size)
			#writeQueue.put(res)
		return

	# download scripts
	def _download(self, RES):
		try:
			des = RES['path']+'/'+RES['filename']
			msg = urllib.urlretrieve(RES['source'], des, reporthook = self.reporthook)
		except Exception, e:
			print e
		sys.stdout.flush()
		return True

	# excute command with script & RES['source']
	def _exec(self, RES):
		path = 'cd '+ RES['path'] + ' && '+ RES['Command']
		try:
			global writeQueue
			res = os.popen(path).readlines()
			writeQueue.put(res) # put result to nsq
		except Exception,e:
			return e

	# excute command without script & RES['source']
	def _exec_1(self, RES):
		path = RES['Command']
		try:
			global writeQueue
			res = os.popen(path).readlines()
			writeQueue.put(res) # put result to nsq
		except Exception,e:
			return e

	def run(self):
		time.sleep(2)		
		while(1):
			global writeQueue
			tmp = self.data.get(1).body
			try:
				RES = json.loads(tmp)
			except Exception,e:
				print e
			des = RES['path']+'/'+RES['filename']

			if os.path.exists(RES['path']):
				if os.path.exists(des): # whether script exists
					retcode = self._exec(RES)
				elif RES['source'] != None: # whether needs to download source file
					self._download(RES)
					retcode = self._exec(RES)
				else: # excute RES['Command'] directly without preparation
					retcode =  self._exec_1(RES)
			else:
				os.makedirs(RES['path'])
				if os.path.exists(des):
					retcode = self._exec(RES)
				elif RES['source'] != None:
					self._download(RES)
					retcode = self._exec(RES)
				else:
					retcode =  self._exec_1(RES)

#multi threads
def foo():
	global readQueue, writeQueue
	try:
		lookupd_address = os.getenv('lookupd')
		nsqd_address = os.getenv('nsqd')
		mysql_port = os.getenv('MYSQL_PORT')
		mysql_host = ''.join(os.popen("ifconfig bond0 | sed -n '/inet addr/p' | awk -F'[: ]+' '{print $4}'").read()).strip('\n')
		request_topic = mysql_host+':'+mysql_port+'_mysql_request'
		response_topic = 'mysql_response'

		if lookupd_address:
			r = Reader('Reader.', readQueue, lookupd_address, request_topic)
		else:
			r = Reader(t_name = 'Reader.', queue=readQueue)#, topic=request_topic)

		if nsqd_address:
			w = Writer('Writer.', writeQueue, nsqd_address, response_topic)
		else:
			w = Writer(t_name='Writer.', queue=writeQueue)#, topic=response_topic)

		e = Execute('Execute.', readQueue)
	except Exception, e:
		print e

	try:
		r.start()
		w.start()
		e.start()
	except Exception,e:
		print 'thread start error',e

	try:
		nsq.run()
	except Exception,e:
		print 'nsq run error',e

	try:
		r.join()
		w.join()
		e.join()
	except Exception,e:
		print 'thread join error',e

#daemon process
def main():
	p = Process(target=foo)
	#p.daemon = True
	p.start()
	p.join()

if __name__ == '__main__':
	main()
