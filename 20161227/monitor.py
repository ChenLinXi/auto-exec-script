#!/usr/bin/env python
#coding: utf-8

import sys, os, time, atexit, string, signal
from signal import SIGTERM


class Daemon:
	def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile

	def _daemonize(self):
		try:
			pid = os.fork()
			if pid > 0:
				sys.exit(0)
		except OSError, e:
			sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
			sys.exit(1)
		
		os.chdir("/")   # change directory 
		os.setsid()     # set a new link
		os.umask(0)     # reset file permission

		try:
			pid = os.fork()
			if pid > 0:
				sys.exit(0)
		except OSError, e:
			sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
			sys.exit(1)

		# redirect file descritor
		sys.stdout.flush()
		sys.stderr.flush()
		si = file(self.stdin, 'r')
		so = file(self.stdout, 'a+')
		se = file(self.stderr, 'a+', 0)
		os.dup2(si.fileno(), sys.stdin.fileno())
		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())

		# register exit func
		atexit.register(self.delpid)
		pid = str(os.getpid())
		file(self.pidfile,'w+').write('%s\n' % pid)

	def delpid(self):
		os.remove(self.pidfile)

	def start(self):
		# check pid file to verify whether the process exits or not 
		try:
			pf = file(self.pidfile, 'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if pid:
			message = 'pidfile %s already exist. Daemon already running!\n'
			sys.stderr.write(message % self.pidfile)
			sys.exit(1)

		# start monitor
		self._daemonize()
		self._run()

	def stopChild(self):
		processInfo = os.popen("ps -ef|grep exec.py|grep -v grep|awk '{print $2}'").readlines()
		for pid in processInfo:
			os.kill(int(pid), signal.SIGKILL)

	def stopParent(self):
		parentList = os.popen("ps -ef|grep monitor.py|grep -v grep|awk '{print $2}'").readlines()
		for pid in parentList:
			os.kill(int(pid), signal.SIGKILL)

	# stop parent process except daemon
	def _stopParent(self):
		index = 0
		parentList = os.popen("ps -ef|grep monitor.py|grep -v grep|awk '{print $2}'").readlines()
		for pid in parentList:
			index += index
			if(index):
				os.kill(int(pid), signal.SIGKILL)

	def stopAll(self):
		# get pid from pid file
		try:
			pf = file(self.pidfile, 'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = 'pidfile %s does not exist. Daemon not running!\n'
			sys.stderr.write(message % self.pidfile)
			return
		try:
			while 1:
				os.kill(pid, SIGTERM)
				time.sleep(0.1)
		except OSError, err:
			err = str(err)
			if err.find('No such process') > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
			else:
				print str(err)
				sys.exit(1)

		# kill child process
		self.stopChild()
		# kill parent process included daemon
		self.stopParent
		# remove log info when daemon exits
		os.system('rm -rf  /tmp/watch_stdout.log')

	def restart(self):
		self.stopChild()
		self._stopParent()
		time.sleep(2)
		self.start()

	def _run(self):
		while True:
			# scripts built-in container
			os.system('cd /root/monitor && python exec.py')
			sys.stdout.flush() 
			time.sleep(2)

if __name__ == '__main__':
	daemon = Daemon('/tmp/watch_process.pid', stdout = '/tmp/watch_stdout.log')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stopAll()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		else:
			print 'unknown command'
			sys.exit(2)
		sys.exit(0)
	else:
		print 'usage: %s start|stop|restart' % sys.argv[0]
		sys.exit(2)
