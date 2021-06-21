#!/usr/bin/env python3
# coding:utf-8
import CloudFlare
import requests
import os
import sys 
import time 
import telnetlib
import yaml
cache={}
with open('config.yml')as f:
	config = yaml.load(f,Loader=yaml.SafeLoader)
def UpdateZones():
	global config
	# print(config)
	# exit()
	cf = CloudFlare.CloudFlare(email=config['CloudFlare']['mail'], token=config['CloudFlare']['token'])
	zone_info = cf.zones.get(params={'name': config['domain']['name']})[0]
	zone_id = zone_info['id']
	body=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"\n"
	#删除记录
	for subdomain in config['domain']['zone']:
		if(subdomain['subdomain']=="@"):
			domain=config['domain']['name']
		else:
			domain=subdomain['subdomain']+"."+config['domain']['name']
		remote_dns_records = cf.zones.dns_records.get(zone_id, params={'name':domain})
		for dns_record in remote_dns_records:
			#只删除 AAAA A CNAME 记录类型
			if(dns_record['type'] in ['AAAA','A','CNAME']):
				if eval(subdomain['type']+"SurvivalScan('"+dns_record['content']+"',"+str(subdomain['port'])+")")==False:
					body=body+("[-] del type [%s] | name [%s] | content [%s]" % (dns_record['type'],dns_record['name'],dns_record['content']))+"\n"
					dns_record_id = dns_record['id']
					r = cf.zones.dns_records.delete(zone_id, dns_record_id)
					#添加记录
		remote_dns_records = cf.zones.dns_records.get(zone_id, params={'name':domain})
		handle_remote_dns_records = []
		for dns_record in remote_dns_records:
			handle_remote_dns_records.append({'name': dns_record['name'].rsplit(dns_record['zone_name'])[0][0:-1], 'type': dns_record['type'], 'content': dns_record['content'], 'proxied': False})
		for dns_record in config['records']:
			#print(dns_record)
			#print(handle_remote_dns_records)
			if	dns_record not in handle_remote_dns_records:
				cachekey = subdomain['type']+"SurvivalScan:"+dns_record['content']+":"+str(subdomain['port'])
				#print(cachekey)
				if (cachekey not in cache.keys()) or (cachekey in cache.keys() and cache[cachekey] != False):
					#print(subdomain['type']+"SurvivalScan('"+dns_record['content']+"',"+str(subdomain['port'])+")")
					if eval(subdomain['type']+"SurvivalScan('"+dns_record['content']+"',"+str(subdomain['port'])+")")==True:
						body=body+("[+] add type [%s] | name [%s] | content [%s]" % (dns_record['type'],dns_record['name'],dns_record['content']))+"\n"
						r = cf.zones.dns_records.post(zone_id, data=dns_record)
						if(dns_record['type']=="CNAME"):
							break
			else:
				print("[-] "+dns_record['content']+" exists in "+ domain)
		if(body.count("type")>0):
			#sendmail(body)
			print(body)
		else:
			print("[-] nothing to do")

def httpSurvivalScan(ip,port=80):
	global cache
	try:
		r=requests.get('http://'+ip+":"+str(port),timeout=2).status_code
		cache[__name__+":"+ip+":"+str(port)] = True
		return True
	except:
		cache[__name__+":"+ip+":"+str(port)] = False
		return False
def icmpSurvivalScan(ip,port=80):
	global cache
	plat=sys.platform
	if (plat=="linux"):
		x=os.popen("ping %s -c 3" %(ip,))
		ping = x.read()
		x.close()
		if int(ping.split("%")[0].split(",")[-1].strip()) > 50:
			cache[__name__+":"+ip+":"+str(port)] = False
			return False
	elif(plat.count("win")!=0):
		x=os.popen("ping %s " %(ip,))
		ping = x.read()
		x.close()
		if int(ping.split("%")[0].split("(")[-1].strip()) == 50:
			cache[__name__+":"+ip+":"+str(port)] = False
			return False
	else:
		exit()
	cache[__name__+":"+ip+":"+str(port)] = True
	return True
def tcpSurvivalScan(ip,port=80):
	global cache
	try:
		telnetlib.Telnet(host=ip, port=port,timeout=2)
		cache[__name__+":"+ip+":"+str(port)] = True
		return True
	except:
		cache[__name__+":"+ip+":"+str(port)] = False
		return False

def main():
	
	print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
	UpdateZones()
	print("[+] Done")
		
if __name__ == '__main__':
	main()


