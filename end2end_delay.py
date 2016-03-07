#!/usr/bin/python

from socket import *
import time
import datetime
import sys
import struct
import binascii
import copy

class Client():
	"""
	This class is the client. It sends pure ethernet frames with a current
	timestamp as payload on the given interface for the given duration in 
	seconds
	"""
	def __init__(self, config, interface = "eth2"):
		"""
		Constructor
		interface - String, e.g., eth2
		config - Dict: the read configuration from config.txt
		"""
		self.interface = interface
		self.config = config
		
		duration = int(self.config['duration'])
		warm_up = int(self.config['warm_up_packets'])
		
		print "Client is sending warm-up packets for {} seconds\n".format(warm_up)

		
		print "Client is sending packets for {} seconds\n".format(duration)
		#define a common eth_type
		self.eth_type = "\x08\x00"
		self.src_mac = "\x00\x00\x00\x00\x00\x01"
		self.dst_mac = "\x00\x00\x00\x00\x00\x02"	
		
		#send packets in each second for 'duration' seconds
		for i in range(0,duration + warm_up):
			#get current timestamp
			ts = datetime.datetime.now()
			#send packet and print it to stdout
			if (i < warm_up):
				print "Sent {}. {}-byte warm-up Ethernet packets on {} with ts={}".format((i+1),self.sendeth(str(ts)), interface, str(ts))
			else:
				print "Sent the {}. {}-byte Ethernet packet on {} with ts={}".format((i+1-warm_up),self.sendeth(str(ts)), interface, str(ts))
			time.sleep(1.0)

		#send a DONE payload in order to indicate the end of stream
		print "Sent {}-byte Ethernet packet on eth0 with payload DONE".format(self.sendeth("DONE"))
		
	def sendeth(self,payload):
		"""
		Send raw Ethernet packet on interface with src_mac and dst_mac
		payload String - the timestamp as string to be sent
		"""
		
		assert(len(self.eth_type) == 2) # 16-bit ethernet type

		s = socket(AF_PACKET, SOCK_RAW)

		#bind the interface to the socket
		s.bind((self.interface, 0))
		
		#send packet
		return s.send(self.dst_mac + self.src_mac + self.eth_type + payload)




class Server():
	"""
	This is the server. It listens on the given interface for the packets
	sent by the client.
	"""
	def __init__(self,config, interface = "eth3"):
		"""
		Constructor
		interface - String, e.g., eth3
		config - Dict: the read configuration from config.txt
		"""
		self.interface = interface
		self.config = config
		self.warm_up = int(self.config["warm_up_packets"])
		
		self.s = socket(AF_PACKET, SOCK_RAW, htons(0x0800))
		self.s.bind((interface,0))

		#a list for storing the measured delay (sent - recv. timestamp)
		self.delay = list()
		
	
	def listen(self):
		"""
		This function is actually doing the main job of the server.
		It is listening on the given interface until Client sends a 'DONE'
		message as payload.
		"""
		number_of_recv_packets = 0
		
		print("Listening on interface {}".format(self.interface))
		closingPayload = ""
		self.run = True
		#we need to check the beginning of payload, since in case of DONE,
		#only 18-byte packet is sent, however, we read 40 bytes in each phase
		#(timestamps as payloads as ethernet packets are of length 40-byte)
		while self.run :
			#packet received (40 byte read)
			receivedPacket = self.s.recv(40)
			#updating #warm_up packets
			number_of_recv_packets += 1
			if (number_of_recv_packets < (self.warm_up + 1)):
				#warm-up phase
				print("{} warm-up packets received".format(number_of_recv_packets))
				continue
				
			#~ elif(number_of_recv_packets == (self.warm_up)):
				#~ #print a dashed line to indicate measurement has started
				#~ print("----------------------------------\n")
			
			#get timestamp immediately before parsing the received packet
			recv_ts=datetime.datetime.now()
			
			#parsing ethernet header - first 14 octet
			ethernetHeader = receivedPacket[0:14]
			#parsing the first 14 octet
			#6byte - dst.mac, 6byte - src.mac, 2byte-eth_type
			ethrheader=struct.unpack("!6s6s2s",ethernetHeader)
			dst_mac = binascii.hexlify(ethrheader[0])
			src_mac = binascii.hexlify(ethrheader[1])
			eth_type = binascii.hexlify(ethrheader[2])
			#payload is the rest
			closingPayload = str(receivedPacket[14:])
			if closingPayload.startswith("DONE"):
				#update the loops condition if we received a 'DONE'
				self.run = False
			else:
				#otherwise, calculate delay
				sent_ts=datetime.datetime.strptime(str(closingPayload), 
																					 "%Y-%m-%d %H:%M:%S.%f")
				print "\nSent timestamp: {}".format(sent_ts)
				print "Recv timestamp: {}\n".format(str(recv_ts)) 
				diff = recv_ts - sent_ts
				#multiply it with 1000 to get millisecs instead of secs
				diff_in_millisec = diff.total_seconds() * 1000
				print "Diff: {} ms".format(diff_in_millisec)
				#store delays in a list for further processing
				self.delay.append(diff_in_millisec)
		#close socket
		self.s.close()
		
	def calculate_delay(self):
		"""
		This function calculates the min, avg, and max delays
		"""
		#let min_delay be the first item in the list and update it later
		min_delay = self.delay[0]
		#let max_delay be the first item as well
		max_delay = min_delay
		#length of the list
		l = len(self.delay)
		#define avg_delay
		avg_delay = 0.0
		
		for i in self.delay:
			if(i < min_delay):
				#update min_delay
				min_delay = copy.deepcopy(i)
			
			if(i > max_delay):
				#update max_delay
				max_delay = copy.deepcopy(i)
			
			#add delays (i) to avg_delay
			avg_delay += i
		
		#calculate avg_delay
		avg_delay = avg_delay / l
		print("\n\n")
		print("Delays:\nMin: {} ms\nAvg:{} ms\nMax:{} ns\n".format(min_delay, 
																															 avg_delay,
																															 max_delay))
																												
if __name__ == "__main__":
	
	if len(sys.argv) < 3:
		print "usage: ./end2end_delay.sh <mode> <interface>"
		print "mode: client/server"
		print "interface: eth2"
		exit(-1)
	
	
	mode = sys.argv[1]
	interface = sys.argv[2]
	
	#configuration dictionary containing the number of packets to be sent
	#and the number of warm-up packets (see config.txt for more details)
	config = dict()
	
	print "Reading and parsing config file..."
	#getting duration data from file
	with open('config.txt', 'r') as lines:
		for line in lines:
			#remove blank lines
			line = line.strip()
			#omit commented lines
			if line:
				if not (line.startswith("#",0,1)):
					#split config params
					key_value = line.split("=")
					#get the key
					key = key_value[0]
					#get the value
					value = key_value[1]
					#push them into the config dictionary as key-value pairs
					config[key]=value
					
	print "Starting {} mode".format(mode)
	if mode == "client":		
		client = Client(config, interface)
	else:
		server = Server(config, interface)
		server.listen()
		server.calculate_delay()
		exit(0)
		
	
