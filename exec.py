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
#block Queue
readQueue = Queue.Queue(0)
writeQueue = Queue.Queue(0)

class Reader(threading.Thread):
    def __init__():
    
    def writeQ():
    
    def run():

class Writer(threading.Thread):
    def __init__():
    
    def pub_message(self):
    
    def finish_pub(self, conn, res):
    
    def run(self):
    
class Execute(threading.Thread):   
    def __init__():
    
    def reporthook(self, block_read, block_size, total_size):
		global writeQueue
		if not block_read:
			res = "connection opened"
			#writeQueue.put(res)
			return
		if total_size<0:
			print "read %d blocks (%dbytes)" %(block_read,block_read*block_size)
			res = 'read ' + str(block_read) + ' blocks (' + str(block_read*block_size) + 'bytes)'
			#writeQueue.put(res)
		else:
			amount_read=block_read*block_size;
			print 'Read %d blocks,or %d/%d' %(block_read,block_read*block_size,total_size)
			res = 'Read ' + str(block_read) + ' blocks,or ' + str(block_read*block_size) + '*' + str(total_size)
			#writeQueue.put(res)
		return
        
    def _download(self, RES):
    
    def _exec(self, RES):
    
    def run(self):
    

#multi threads
def foo():
	global readQueue, writeQueue
	r = Reader('Reader.', readQueue)
	w = Writer('Writer.', writeQueue)
	e = Execute('Exec.', readQueue)
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
