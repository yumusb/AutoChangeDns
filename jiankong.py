#!/usr/bin/env python3
# coding:utf-8
# @Author: yumu
# @Date:   2019-09-02
# @Email:   yumusb@foxmail.com
# @Last Modified by:   yumu
# @Last Modified time: 2019-09-04
import CloudFlare
import requests
import os
import sys 
import time 
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import yaml
with open('config.yml')as f:
	config = yaml.load(f,Loader=yaml.SafeLoader)
def UpdateZones():
	global config
	cf = CloudFlare.CloudFlare(email=config['CloudFlare']['mail'], token=config['CloudFlare']['token'])
	zone_info = cf.zones.get(params={'name': config['domain']['name']})[0]
	zone_id = zone_info['id']
	body=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"\nDNS记录做出以下修改:\ndel\n"
	#删除记录
	for subdomain in config['domain']['zone']:
		if(subdomain=="@"):
			domain=config['domain']['name']
		else:
			domain=subdomain+"."+config['domain']['name']
		dns_records = cf.zones.dns_records.get(zone_id, params={'name':domain})
		for dns_record in dns_records:
			#只删除 AAAA A CNAME 记录类型
			if(dns_record['type'] in ['AAAA','A','CNAME']):
				if(CheckIp(dns_record['content'])==100):
					body=body+("type [%s] | name [%s] | content [%s]" % (dns_record['type'],dns_record['name'],dns_record['content']))+"\n"
					dns_record_id = dns_record['id']
					r = cf.zones.dns_records.delete(zone_id, dns_record_id)
					body=body+"add\n"
					#添加记录
					for dns_record in config['records']:
						if(CheckIp(dns_record['content'])!=100):
							body=body+("type [%s] | name [%s] | content [%s]" % (dns_record['type'],dns_record['name'],dns_record['content']))+"\n"
							r = cf.zones.dns_records.post(zone_id, data=dns_record)
							if(dns_record['type']=="CNAME"):
								break
					if(body.count("type")>0):
						sendmail(body)

def SurvivalScan(ip):
	r=requests.get('http://'+url,timeout=10).status_code
	return r
'''
@description: 利用PING检测IP存活
@param {type} IP地址
@return: 丢包率(ping命令返回的 100% loss)
'''
def CheckIp(ip):
	plat=sys.platform
	if (plat=="linux"):
		x=os.popen("ping %s -c 3" %(ip,))
		ping = x.read()
		x.close()
		return int(ping.split("%")[0].split(",")[-1].strip())

	elif(plat.count("win")!=0):
		x=os.popen("ping %s " %(ip,))
		ping = x.read()
		x.close()
		return int(ping.split("%")[0].split("(")[-1].strip())
	else:
		exit()
def sendmail(body):
	global config
	mail_host=config['SMTP']['host']  #设置服务器
	mail_user=config['SMTP']['user']    #用户名
	mail_pass=config['SMTP']['pass']   #口令 

	sender = mail_user
	receivers = config['SMTP']['receivers']
	message = MIMEText(body, 'plain', 'utf-8')
	message['From'] = sender
	message['To'] = receivers
	subject = 'DNS记录更换'
	message['Subject'] = Header(subject, 'utf-8')
	try:
	    smtpObj = smtplib.SMTP() 
	    smtpObj.connect(mail_host, 25)    # 25 为 SMTP 端口号
	    smtpObj.login(mail_user,mail_pass)  
	    smtpObj.sendmail(sender, receivers, message.as_string())
	    print("send Mail Success")
	    return True
	except smtplib.SMTPException:
	    return False
def main():
	while True:
		print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
		UpdateZones()
		time.sleep(300)
		
if __name__ == '__main__':
	main()


