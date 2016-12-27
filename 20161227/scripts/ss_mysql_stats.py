#!/usr/bin/env python
#coding=utf-8

import sys
import os,json
import inspect
import MySQLdb
import MySQLdb.cursors
class GetMysqlStatus():
    def __init__(self):
        self.result = ''
        self.dict = {}
        self.status = 0
    def check(self):
        try:
            self.db = MySQLdb.connect(xxxx)
#        except Exception, e:
#            raise Exception, 'Cannot interface with MySQL server, %s' % e
#	except:
	except Exception, e:
		print "{\"susessful\": \"false\",\"message\": \"1\",\"error\": \"%s\"}" % e
		sys.exit(1)
    def extract(self):
        try:
            c = self.db.cursor()
            c.execute("""show global status;""")
            self.result = c.fetchall()
            for i in self.result:
                self.dict[i['Variable_name']] = i['Value']
            return self.dict
            c.close()
            self.db.close()
        except Exception, e:
                print "{\"susessful\": \"false\",\"message\": \"1\",\"error\": \"%s\"}" % e
                sys.exit(1)
    def extract_1(self):
        try:
            d = self.db.cursor()
            d.execute("""show variables like 'max_connections';""")
            self.result = d.fetchall()
            for i in self.result:
                self.dict[i['Variable_name']] = i['Value']
            return self.dict
            d.close()
            self.db.close()
        except Exception, e:
                print "{\"susessful\": \"false\",\"message\": \"1\",\"error\": \"%s\"}" % e
                sys.exit(1)
    def extract_2(self):
        try:
            e = self.db.cursor()
            e.execute(" SHOW SLAVE STATUS ")
            result = e.fetchall()
            if len(result) == 0:
                self.status = -1
                return self.status
            else:
                self.status = 1
                return result[0]['Seconds_Behind_Master']
            e.close()
            self.db.close()
        except Exception, e:
                print "{\"susessful\": \"false\",\"message\": \"1\",\"error\": \"%s\"}" % e
                sys.exit(1)
    def extract_3(self):
        try:
            f = self.db.cursor()
            f.execute("""show variables like 'innodb_buffer_pool_size';""")
            self.result = f.fetchall()
            for i in self.result:
                self.dict[i['Variable_name']] = i['Value']
            return self.dict
            f.close()
            self.db.close()
        except Exception, e:
                print "{\"susessful\": \"false\",\"message\": \"1\",\"error\": \"%s\"}" % e
                sys.exit(1)
    def Innodb_buffer_usage(self):
	try:
            Innodb_buffer_usage = round((1 - float(self.dict['Innodb_buffer_pool_pages_free']) / float(self.dict['Innodb_buffer_pool_pages_total'])) * 100,2)
        except Exception, e:
                print "{\"susessful\": \"false\",\"message\": \"1\",\"error\": \"%s\"}" % e
                sys.exit(1)
        return Innodb_buffer_usage
    def get_val(self, key):
        return self.dict[key]

class ErrorOut():
    def error_print(self):
        print "{\"susessful\": \"false\",\"message\": \"1\",\"error\": \"error\"}"
        sys.exit(1)
class Main():
    def main(self):
        attr = ['Com_select','Com_update','Com_insert','Com_delete','Aborted_clients','Aborted_connects','Threads_running','Threads_connected','Threads_created',
            'Threads_cached', 'max_connections', 'Connections','Slaves_running','Slave_running','innodb_buffer_pool_size']
        res = {}
        error = ErrorOut()
	a = GetMysqlStatus()
        a.check()
	a.extract()
	a.extract_1()
	a.extract_3()
        i = 0
        for i in range(len(attr)):
		if hasattr(a, attr[i]):
			res[attr[i]] = getattr(a, attr[i])()
	        else:
                	res[attr[i]] = a.get_val(attr[i])
        usage = a.Innodb_buffer_usage()
        res["Innodb_buffer_usage"] = str(usage)
        status = a.extract_2()
        if status == -1:
		res["Role"] = "Master"
		res["Seconds_Behind_Master"] = "0"
	else:
                res["Role"] = "Slave"
                res["Seconds_Behind_Master"] = str(status)
            	usage = a.Innodb_buffer_usage()
		res["Innodb_buffer_usage"] = str(usage)
        res_json = json.dumps(res, indent=4).encode("utf-8")
	res1 = {}
	res1["Sucessful"] = "ture"
	res1["Message"] = res
	res1["error"] = "OK"
        res1_json = json.dumps(res1, indent=4).encode("utf-8")
        print res1_json
if __name__ == "__main__":
     run = Main()
     run.main()
