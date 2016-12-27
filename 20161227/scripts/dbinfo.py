import os
import nsq
import tornado.ioloop
import time

class WriterTest():

	def __init__(self):
		self.topic = 'Mysql_Monitor'
		self.writer = nsq.Writer(['nsqd-address'])

	def get_info(self):
		path = xxxx
		res = os.popen(path).read()
		#print res
		return res

	def pub_message(self):
		self.writer.pub(self.topic, self.get_info(), self.finish_pub)

	def finish_pub(self, conn, data):
		#print data
		pass

	def _exec(self):
		tornado.ioloop.PeriodicCallback(self.pub_message, 10000).start()
		nsq.run()

if __name__ == '__main__':
	wt = WriterTest()
	wt._exec()

