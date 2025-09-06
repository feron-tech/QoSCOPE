import statistics
import math
import time
import pandas as pd
from helper import Helper
import gparams
from orchestrator import Orchestrator, VethOrchestrator
import socket
import time
import subprocess
import os
import pyshark
import json
from icmplib import ping, multiping, traceroute, resolve
from icmplib import async_ping, async_multiping, async_resolve
from icmplib import ICMPv4Socket, ICMPv6Socket, AsyncSocket, ICMPRequest, ICMPReply
from icmplib import ICMPLibError, NameLookupError, ICMPSocketError
from icmplib import SocketAddressError, SocketPermissionError
from icmplib import SocketUnavailableError, SocketBroadcastError, TimeoutExceeded
from icmplib import ICMPError, DestinationUnreachable, TimeExceeded
from io import StringIO
import psutil

class Backend:
	def __init__(self):
		# help functions and params
		self.helper = Helper()
		self.cnt_exp=0
		self.cnt_repet=0
		self.df_out_monitor=None

		# init functions
		res=self.init_dbs()
		if res is None:
			return

		# read user input
		res=self.read_input()
		if res is None:
			return

		# run campaign
		self.db_in_user = res # python translates str booleans to Python types
		self.run_campaign()

	def kill_process_tree(self,pid, including_parent=True):
		parent = psutil.Process(pid)
		children = parent.children(recursive=True)
		for child in children:
			child.kill()
		gone, still_alive = psutil.wait_procs(children, timeout=5)
		if including_parent:
			parent.kill()
			parent.wait(5)

	def init_dbs(self):

		mydbs=[
			gparams._DB_FILE_LOC_OUT_LOG,
			gparams._RES_FILE_LOC_TWAMP,
			gparams._RES_FILE_LOC_OWAMP,
			gparams._RES_FILE_LOC_UDPPING,
			gparams._RES_FILE_LOC_ICMP,
			gparams._RES_FILE_LOC_IPERF,
			gparams._RES_FILE_LOC_PHY,
			gparams._RES_FILE_LOC_PHY_RAW,
			gparams._RES_FILE_LOC_APP,
			gparams._RES_FILE_LOC_GUI_APP,
		]

		if gparams._LOCAL_TEST:
			pass
		else:
			mydbs.append(gparams._DB_FILE_LOC_IN_USER)


		for el in mydbs:
			res=self.helper.init_db(loc=el,header=None)
			if res is None:
				return None

		return 200

	def read_input(self):
		res=None
		attempt = 1
		while (res is None):
			print('(Backend) DBG: Reading input sources (attempt='+str(attempt)+')...')

			if attempt>1:
				self.helper.wait(gparams._WAIT_SEC_BACKEND_READ_INPUT_SOURCES)

			res=self.helper.read_json2dict(loc=gparams._DB_FILE_LOC_IN_USER)
			attempt=attempt+1

			if attempt>=gparams._ATTEMPTS_BACKEND_READ_INPUT_SOURCES:
				print('(Backend) ERROR: Cannot read input sources!')
				return None

		print('(Backend) DBG: Read input sources - Success')
		return res

	def run_campaign(self):
		try:
			_camp_repet=int(self.db_in_user['Measurement']['Repetitions per campaign'])
			_camp_gap_hours = float(self.db_in_user['Measurement']['Repetition time gap (hours)'])
			_camp_name = self.db_in_user['Measurement']['Campaign name']
			_exp_num=int(self.db_in_user['Measurement']['Experiments per campaign'])

			print('*** *** *** *** *** *** *** *** *** ***')
			my_event=('Initiating campaign='+str(_camp_name)+
			          ',repet='+str(_camp_repet)+
			          ',gap='+str(_camp_gap_hours)+
			          ',exps='+str(_exp_num))
			print('(Backend) DBG: '+str(my_event))

			myjson_line=gparams._DB_FILE_FIELDS_OUT_LOG
			myjson_line['time']=self.helper.get_str_timestamp()
			myjson_line['description']=my_event
			self.helper.write_dict2json(loc=gparams._DB_FILE_LOC_OUT_LOG,mydict=myjson_line,clean=False)

		except Exception as ex:
			print('(Backend) ERROR: At input settings=' + str(ex))
			return None

		self.cnt_repet=0
		while (self.cnt_repet<_camp_repet):

			# start new campaign repetition
			self.cnt_exp=0
			for i in range(0,_exp_num):
				# start new experiments inside the campaign repetition
				self.run_exp()
				self.cnt_exp = self.cnt_exp +1

			self.cnt_repet=self.cnt_repet+1

			# check if still not finished
			if (self.cnt_repet < _camp_repet):
				# check waiting time between campaign repetitions
				asctime_start=self.helper.get_curr_asctime()
				total_wait_time_sec=int(3600*_camp_gap_hours)
				wait_interval_sec=int(total_wait_time_sec/20)

				remaining_time_sec=1
				while (remaining_time_sec>0):
					asctime_curr = self.helper.get_curr_asctime()
					remaining_time_sec = (total_wait_time_sec -
					                      self.helper.diff_asctimes_sec(early=asctime_start,late=asctime_curr))

					if (remaining_time_sec>0):
						my_event = ('Remaining time for next repetition (sec):' + str(remaining_time_sec))
						print('(Backend) DBG: ' + str(my_event))

						myjson_line = gparams._DB_FILE_FIELDS_OUT_LOG
						myjson_line['time'] = self.helper.get_str_timestamp()
						myjson_line['description'] = my_event
						self.helper.write_dict2json(loc=gparams._DB_FILE_LOC_OUT_LOG, mydict=myjson_line,clean=False)

						self.helper.wait(wait_interval_sec)

		# print completion msg
		my_event = 'Completed campaign:' + str(_camp_name)
		print('(Backend) DBG: ' + str(my_event))
		print('*** *** *** *** *** *** *** *** *** ***')

		myjson_line = gparams._DB_FILE_FIELDS_OUT_LOG
		myjson_line['time'] = self.helper.get_str_timestamp()
		myjson_line['description'] = my_event
		self.helper.write_dict2json(loc=gparams._DB_FILE_LOC_OUT_LOG, mydict=myjson_line, clean=False)

	def run_exp(self):
		my_event = 'Initiating exp:' + str(self.cnt_exp) + ',of campaign repetition:' + str(self.cnt_repet)
		myjson_line = gparams._DB_FILE_FIELDS_OUT_LOG
		myjson_line['time'] = self.helper.get_str_timestamp()
		myjson_line['description'] = my_event
		self.helper.write_dict2json(loc=gparams._DB_FILE_LOC_OUT_LOG, mydict=myjson_line, clean=False)

		print('--- --- --- --- --- --- --- --- ---')
		print('(Backend) DBG: ' + my_event)



		self.get_baseline_measurements()
		self.get_app_measurements()

		my_event = 'Completed exp:' + str(self.cnt_exp) + ',of campaign repetition:' + str(self.cnt_repet)
		myjson_line = gparams._DB_FILE_FIELDS_OUT_LOG
		myjson_line['time'] = self.helper.get_str_timestamp()
		myjson_line['description'] = my_event
		self.helper.write_dict2json(loc=gparams._DB_FILE_LOC_OUT_LOG, mydict=myjson_line, clean=False)

		print('(Backend) DBG: ' + my_event)
		print('--- --- --- --- --- --- --- --- ---')

	def get_app_measurements(self):
		# remove left-over containers - todo
		#orch = Orchestrator()
		#res=orch.clean_all()
		#if res is None:
		#	print('(Backend) ERROR at container clean - exit app measurements')
		#	return None

		self.get_app_mqtt()
		self.get_app_video()
		self.get_app_profinet()

	def get_app_mqtt_old(self):
		try:
			_enable=self.db_in_user['Experiment']['Application']['MQTT']['enable']
			_payload_bytes=int(self.db_in_user['Experiment']['Application']['MQTT']['payload (bytes)'])
			_interval_ms=float(self.db_in_user['Experiment']['Application']['MQTT']['interval (ms)'])
			_shark_captime_sec=int(self.db_in_user['Experiment']['Application']['Wireshark']['capture time (sec)'])
			_shark_max_packs=int(self.db_in_user['Experiment']['Application']['Wireshark']['max packets'])
			_camp_name=self.db_in_user['Measurement']['Campaign name']
			_server_ip=self.db_in_user['Network']['Server IP']

			if _enable == 'False':
				print('(Backend) DBG: MQTT test deactivated')
				return None
			else:
				print('(Backend) DBG: Init MQTT test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init MQTT: '+str(ex))
			return None

		sleep_sec=_interval_ms*1e-3

		config_dict={
			'app_name':'MQTT',
			'client_app_cmd': './client_mqtt',
			'camp_name':_camp_name,
			'env':{
				'ENV_SERVER_IP' : _server_ip,
				'ENV_SERVER_PORT' : gparams._PORT_SERVER_MQTT1,
				'SLEEP_SEC' : sleep_sec,
				'MAX_PAYLOAD_SIZE_BYTES' : _payload_bytes
			},
			'shark_captime_sec':_shark_captime_sec,
			'shark_max_packs': _shark_max_packs,
		}

		res=self.activate_app(config_dict=config_dict)


	def get_app_mqtt(self):
		try:
			_enable = self.db_in_user['Experiment']['Application']['MQTT']['enable']
			_payload_bytes = int(self.db_in_user['Experiment']['Application']['MQTT']['payload (bytes)'])
			_interval_ms = float(self.db_in_user['Experiment']['Application']['MQTT']['interval (ms)'])
			_shark_captime_sec = int(self.db_in_user['Experiment']['Application']['Wireshark']['capture time (sec)'])
			_shark_max_packs = int(self.db_in_user['Experiment']['Application']['Wireshark']['max packets'])
			_camp_name = self.db_in_user['Measurement']['Campaign name']
			_server_ip = self.db_in_user['Network']['Server IP']

			if _enable == 'False':
				print('(Backend) DBG: MQTT test deactivated')
				return None
			else:
				print('(Backend) DBG: Init MQTT test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init MQTT: ' + str(ex))
			return None

		sleep_sec = _interval_ms * 1e-3

		# Build command string to run your MQTT client script inside the namespace
		mqtt_script_path = 'client_app_mqtt.py'  # adjust path accordingly
		client_app_cmd = f"{gparams._CONDA_EXEC} {mqtt_script_path}"

		config_dict = {
			'app_name': 'MQTT',
			'client_app_cmd': client_app_cmd,
			'camp_name': _camp_name,
			'env': {
				'ENV_SERVER_IP': _server_ip,
				'ENV_SERVER_PORT': '1883',
				'SLEEP_SEC': sleep_sec,
				'MAX_PAYLOAD_SIZE_BYTES': _payload_bytes
			},
			'shark_captime_sec': _shark_captime_sec,
			'shark_max_packs': _shark_max_packs,
		}

		res = self.activate_app(config_dict=config_dict)


	def get_app_video(self):
		try:
			_enable = self.db_in_user['Experiment']['Application']['Video']['enable']
			_fps = int(self.db_in_user['Experiment']['Application']['Video']['fps'])
			_width = int(self.db_in_user['Experiment']['Application']['Video']['width'])
			_height = int(self.db_in_user['Experiment']['Application']['Video']['height'])
			_shark_captime_sec = gparams._SHARK_VIDEO_TIME_SEC
			_shark_max_packs = gparams._SHARK_VIDEO_PACKS
			_camp_name = self.db_in_user['Measurement']['Campaign name']
			_server_ip = self.db_in_user['Network']['Server IP']

			if _enable == 'False':
				print('(Backend) DBG: Video test deactivated')
				return None
			else:
				print('(Backend) DBG: Init Video test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init Video: ' + str(ex))
			return None

		video_script_path = 'client_app_video_ul.py'  # or whatever your video client script is called

		client_app_cmd = f"{gparams._CONDA_EXEC} {video_script_path}"

		config_dict = {
			'app_name': 'video',
			'client_app_cmd': client_app_cmd, 
			'camp_name': _camp_name,
			'env': {
				'ENV_SERVER_IP': _server_ip,
				'ENV_SERVER_PORT': str(gparams._PORT_SERVER_OPENCV),  # ensure it's a string
				'ENV_FPS': str(_fps),
				'ENV_FRAME_WIDTH': str(_width),
				'ENV_FRAME_HEIGHT': str(_height),
			},
			'shark_captime_sec': _shark_captime_sec,
			'shark_max_packs': _shark_max_packs,
		}

		return self.activate_app(config_dict=config_dict)

	def get_app_video_old(self):
		try:
			_enable=self.db_in_user['Experiment']['Application']['Video']['enable']
			_fps=int(self.db_in_user['Experiment']['Application']['Video']['fps'])
			_width=int(self.db_in_user['Experiment']['Application']['Video']['width'])
			_height = int(self.db_in_user['Experiment']['Application']['Video']['height'])
			_shark_captime_sec=gparams._SHARK_VIDEO_TIME_SEC
			_shark_max_packs=gparams._SHARK_VIDEO_PACKS
			_camp_name=self.db_in_user['Measurement']['Campaign name']
			_server_ip = self.db_in_user['Network']['Server IP']

			if _enable == 'False':
				print('(Backend) DBG: Video test deactivated')
				return None
			else:
				print('(Backend) DBG: Init Video test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init Video: '+str(ex))
			return None

		config_dict={
			'app_name':'video',
			'client_app_image_name':'client_stream',
			'camp_name': _camp_name,
			'env':{
				'ENV_SERVER_IP': _server_ip,
				'ENV_SERVER_PORT': gparams._PORT_SERVER_OPENCV,
				'ENV_FPS' : _fps,
				'ENV_FRAME_WIDTH' : _width,
				'ENV_FRAME_HEIGHT' : _height
			},
			'shark_captime_sec':_shark_captime_sec,
			'shark_max_packs': _shark_max_packs,
		}

		res=self.activate_app(config_dict=config_dict)

	def get_app_profinet(self):
		# todo: placeholder for profinet client
		pass

	def activate_app(self, config_dict):
		try:
			_app_name = config_dict['app_name']
			_client_app_cmd = config_dict['client_app_cmd']  # <-- changed from image name to actual command line
			_env = config_dict.get('env', {})
			_shark_captime_sec = config_dict['shark_captime_sec']
			_shark_max_packs = config_dict['shark_max_packs']
			_camp_name = config_dict['camp_name']


			print(f'(Backend) DBG: Activating app={_app_name} in namespace={gparams._NS_NAME}...')
		except Exception as ex:
			print(f'(Backend) ERROR: Activate app: {ex}')
			
		orch = VethOrchestrator()
		orch.create_namespace(gparams._NS_NAME, gparams._VETH_HOST, gparams._VETH_NS, gparams._HOST_IP, gparams._NS_IP, gparams._WWAN_IF)
		proc = orch.activate(client_app_cmd=_client_app_cmd, env=_env)

		# Optionally wait or do pyshark capture on veth_host interface here
		self.get_pyshark_kpis(my_iface=gparams._VETH_HOST, display_filter=None,
						  max_packs=_shark_max_packs,
						  captime_sec=_shark_captime_sec,
						  camp_name=_camp_name,
						  app_name=_app_name)        

		print('(Backend) DBG: Stopping app gracefully...')
		# Now stop the client app process if still running
		if proc.poll() is None:  # process is still running
			proc.terminate()      # or proc.kill() for force stop
			proc.wait()           # wait for termination

		print('(Backend) DBG: Deactivating app in the orchestrator...')
		orch.deactivate(proc)

	def activate_app_deprec(self, config_dict):
		try:
			_app_name = config_dict['app_name']
			_client_app_cmd = config_dict['client_app_cmd']  # <-- changed from image name to actual command line
			_env = config_dict.get('env', {})
			_shark_captime_sec = config_dict['shark_captime_sec']
			_shark_max_packs = config_dict['shark_max_packs']
			_camp_name = config_dict['camp_name']
			print(f'(Backend) DBG: Activating app={_app_name}...')
		except Exception as ex:
			print(f'(Backend) ERROR: Activate app: {ex}...')
			return None

		# activate app using veth orchestrator
		orch = VethOrchestrator()
		iface = orch.activate(command=_client_app_cmd, env=_env)  # note we pass command, not image name

		# monitor stats on returned interface
		self.get_pyshark_kpis(my_iface=iface, display_filter=None,
							  max_packs=_shark_max_packs,
							  captime_sec=_shark_captime_sec,
							  camp_name=_camp_name,
							  app_name=_app_name)

		# deactivate app
		orch.deactivate()


	def activate_app_old(self,config_dict):
		try:
			_app_name=config_dict['app_name']
			_client_app_image_name=config_dict['client_app_image_name']
			_ports_dict=config_dict['ports_dict']
			_env=config_dict['env']
			_shark_captime_sec=config_dict['shark_captime_sec']
			_shark_max_packs=config_dict['shark_max_packs']
			_camp_name=config_dict['camp_name']
			print('(Backend) DBG: Activating app='+str(_app_name)+'...')
		except Exception as ex:
			print('(Backend) ERROR: Activate app:'+str(ex)+'...')
			return None

		# activate app
		orch = VethOrchestrator()
		if _ports_dict is None:
			iface=orch.activate(image=_client_app_image_name, detach=True, env=_env)
		else:
			iface = orch.activate(image=_client_app_image_name, detach=True, env=_env,port_dict=_ports_dict)

		# monitor stats
		self.get_pyshark_kpis(my_iface=iface,display_filter=None,max_packs=_shark_max_packs,
		                      captime_sec=_shark_captime_sec,camp_name=_camp_name,app_name=_app_name)

		# deactivate app
		orch.deactivate(image=_client_app_image_name)

	def get_pyshark_kpis(self,my_iface='Ethernet',display_filter=None,max_packs=5000,
	                     captime_sec=10,camp_name='',app_name=''):
		print('(Backend) DBG: Initiate pyshark kpis ...')

		# hack to get all available veth-xxx interfaces (not supported by Pyshark)
		#my_iface=None
		#try:
		#	# expect this to fail and raise an exception with all available interfaces
		#	cap=pyshark.LiveCapture(interface='this_is_not_an_interface_100_percent!!', display_filter=display_filter)
		#	cap.sniff(timeout=1)
		#except Exception as ex:
		#	print('(Monitor) DBG: Getting available veth interfaces in the system...')
		#	# get all words of the exception str
		#	word_list=str(ex).split()
		#	for el in word_list:
		#		if 'veth' in el:
		#			my_iface=el
		#			break

		#if my_iface is None:
		#	print('(Monitor) ERROR: No veth ifaces found')
		#	return None

		# delete previous left-overs if any
		try:
			os.remove(gparams._SHARK_TEMP_OUT_FILE)
			print('(Backend) DBG: (Previous) temp capture removed OK')
		except Exception as ex:
			print('(Backend) Warning: Temp capture remove='+str(ex))

		if False: # old script for safety
			attempt=1
			res=None
			while (res is None):
				try:
					print('(Backend) DBG: Initiate capture for veth='+str(my_iface)+' (attempt=' + str(attempt) + ')...')
					if attempt > 1:
						self.helper.wait(gparams._WAIT_SEC_BACKEND_READ_INPUT_SOURCES)
					attempt = attempt + 1

					cap = pyshark.LiveCapture(interface=my_iface, display_filter=display_filter,
											  output_file=gparams._SHARK_TEMP_OUT_FILE)
					cap.sniff_continuously()
					res=200
				except:
					if attempt >= 5:
						print('(Backend) ERROR: Cannot find iface in Pyshark!')
						res = 500
			if res!=200:
				print('(Backend) ERROR: Exiting...')
				return None


			try:
				print('(Backend) DBG: Capture for max packs='+str(max_packs)+' OR max duration (sec)='+str(captime_sec)+'...')
				pack_cnt=0
				start_time = time.time()
				sniff_duration_sec=0

				for pack in cap:
					sniff_duration_sec=time.time() - start_time
					if (pack_cnt>max_packs) or (sniff_duration_sec>captime_sec):
						break
					pack_cnt = pack_cnt + 1
				print('(Backend) DBG: Capture OK, final pack_cnt='+str(pack_cnt)+',duration (sec)='+str(sniff_duration_sec))
				print('(Backend) DBG: Breaking capture...')
				cap.close()
			except Exception as ex:
				print('(Backend) ERROR during capture:'+str(ex))


		try:
			print(f'(Backend) DBG: Initiate capture for veth={my_iface} )...')
			cap = pyshark.LiveCapture(interface=my_iface, display_filter=display_filter,
									  output_file=gparams._SHARK_TEMP_OUT_FILE)

			print(f'(Backend) DBG: Will capture for max packs={max_packs} OR max duration (sec)={captime_sec}...')

			pack_cnt = 0
			start_time = time.time()


			for pack in cap.sniff_continuously():
				sniff_duration_sec = time.time() - start_time
				if pack_cnt > max_packs or sniff_duration_sec > captime_sec:
					print('(Backend) DBG: Stopping capture loop due to limits.')
					break
				pack_cnt += 1

			print(f'(Backend) DBG: Capture OK, final pack_cnt={pack_cnt}, duration (sec)={sniff_duration_sec}')

			# Close capture gracefully
			try:
				print('Closing shark gracefully...')
				# cap.close()
			except Exception as e:
				print(f"(Backend) Warning: error closing capture: {e}")

			# Forcibly terminate tshark if still running
			if hasattr(cap, '_running_processes'):
				for proc in cap._running_processes:
					# Check if it's a multiprocessing.Process instance
					if hasattr(proc, 'is_alive'):
						if proc.is_alive():
							print(f'(Backend) DBG: Terminating multiprocessing.Process PID={proc.pid}...')
							proc.terminate()
							proc.join(timeout=5)
							if proc.is_alive():
								print(f'(Backend) DBG: Process PID={proc.pid} still alive after terminate/join.')
					# Else fallback to subprocess.Popen handling
					elif hasattr(proc, 'poll'):
						if proc.poll() is None:
							print(f'(Backend) DBG: Terminating subprocess.Popen PID={proc.pid}...')
							proc.terminate()
							try:
								proc.wait(timeout=5)
							except subprocess.TimeoutExpired:
								print(f'(Backend) DBG: Killing subprocess.Popen PID={proc.pid} after timeout...')
								proc.kill()
								proc.wait()
					else:
						print(f'(Backend) Warning: Unknown process object type {type(proc)}')
			else:
				print('(Backend) Warning: no _running_processes attribute found in cap')


			res = 200

		except Exception as ex:
			print(f'(Backend) ERROR during capture: {ex}')
			res = 500

		if res != 200:
			print('(Backend) ERROR: Exiting...')
			return None


		try:
			min_sniff_timestamp=math.inf
			max_sniff_timestamp = 0
			sum_packet_len_bytes=0
			rtt_list=[]
			max_timestamp='1999-01-01 00:00:00.000000'

			print('(Backend) DBG: Capture analysis...')
			cap = pyshark.FileCapture(input_file=gparams._SHARK_TEMP_OUT_FILE)
			pack_cnt=0
			for pack in cap:
				myjson_line=gparams._RES_FILE_FIELDS_APP

				try:
					myjson_line['camp_name'] = camp_name
				except:
					pass

				try:
					myjson_line['repeat_id'] = str(self.cnt_repet)
				except:
					pass

				try:
					myjson_line['exp_id'] = str(self.cnt_exp)
				except:
					pass

				try:
					res=self.helper.get_str_timestamp()
					myjson_line['timestamp'] = res
					max_timestamp=max(max_timestamp,res)
				except:
					pass

				try:
					myjson_line['app_name'] = app_name
				except:
					pass

				try:
					myjson_line['pack_id'] = str(pack_cnt)
				except:
					pass

				try:
					myjson_line['sniff_time'] = str(pack.sniff_time)
				except:
					pass

				try:
					res=pack.sniff_timestamp
					myjson_line['sniff_timestamp'] = str(res)
					min_sniff_timestamp=min(min_sniff_timestamp,float(res))
					max_sniff_timestamp = max(max_sniff_timestamp, float(res))
				except:
					pass

				try:
					myjson_line['protocol'] = str(pack.highest_layer)
				except:
					pass

				try:
					res=pack.length
					myjson_line['pack_len_bytes'] = str(res)
					sum_packet_len_bytes=sum_packet_len_bytes+int(res)
				except:
					pass

				try:
					myjson_line['addr_src'] = str(pack.ip.src)
				except:
					pass

				try:
					myjson_line['port_src'] = str(pack[pack.transport_layer].srcport)
				except:
					pass

				try:
					myjson_line['addr_dest'] = str(pack.ip.dst)
				except:
					pass

				try:
					myjson_line['port_dest'] = str(pack[pack.transport_layer].dstport)
				except:
					pass

				try:
					res=pack.tcp.analysis_ack_rtt
					myjson_line['rtt'] = str(res)
					rtt_list.append(float(res))
				except:
					pass

				try:
					str_p = str(pack)
					if (
						"TCP Dup ACK" in str_p
						or "TCP Previous" in str_p
						or "TCP Retransmission" in str_p
						or "TCP Fast Retransmission" in str_p
						or "Out-Of-Order" in str_p
						or "TCP Spurious Retransmission" in str_p):
						res = True
					else:
						res = False

					myjson_line['drop_flag'] = str(res)
				except:
					pass

				pack_cnt=pack_cnt+1
				self.helper.write_dict2json(loc=gparams._RES_FILE_LOC_APP, mydict=myjson_line, clean=False)


				if pack_cnt<2:
					print('(Backend) DBG: Capture example pack addr dest='+str(myjson_line['addr_dest']))

			print('(Backend) DBG: Capture read OK')
		except Exception as ex:
			print('(Backend) ERROR: Capture read='+str(ex))

		# write aggregated results to gui_app.json DB for presentation purposes only
		try:
			myjson_line = gparams._RES_FILE_FIELDS_GUI_APP
			time_diff = max_sniff_timestamp - min_sniff_timestamp
			thru_bps = float((sum_packet_len_bytes * 8) / time_diff)

			try:
				myjson_line['RTT (msec)'] = str(statistics.mean(rtt_list)* 1e3)
			except:
				pass

			try:
				myjson_line['app_name'] = app_name
			except:
				pass

			try:
				myjson_line['Throughput (Mbps)'] = str(thru_bps * 1e-6)
			except:
				pass

			try:
				myjson_line['timestamp'] = str(max_timestamp)
			except:
				pass

			self.helper.write_dict2json(loc=gparams._RES_FILE_LOC_GUI_APP, mydict=myjson_line, clean=False)

			print('(Backend) DBG: Capture write OK')
		except Exception as ex:
			print('(Backend) ERROR: Capture write=' + str(ex))

		try:
			os.remove(gparams._SHARK_TEMP_OUT_FILE)
			print('(Backend) DBG: (Previous) temp capture removed OK')
		except Exception as ex:
			print('(Backend) ERROR: Temp capture remove='+str(ex))
			return None

		print('(Backend) DBG: Capture analysis OK')
		return 200


	def get_iperf(self):
		try:
			_enable=self.db_in_user['Experiment']['Baseline']['iperf']['enable']
			_protocol = self.db_in_user['Experiment']['Baseline']['iperf']['protocols']
			_payload_bytes = int(self.db_in_user['Experiment']['Baseline']['iperf']['payload (bytes)'])
			_target_rate_mbps=int(self.db_in_user['Experiment']['Baseline']['iperf']['bitrate (Mbps)'])
			_duration_sec=int(self.db_in_user['Experiment']['Baseline']['iperf']['duration (sec)'])
			_server_ip=self.db_in_user['Network']['Server IP']
			_camp_name=self.db_in_user['Measurement']['Campaign name']

			if _enable=='False':
				print('(Backend) DBG: Iperf test deactivated')
				return None
			else:
				print('(Backend) DBG: Init iperf test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init iperf: '+str(ex))
			return None

		myjson_line = gparams._RES_FILE_FIELDS_IPERF
		myjson_line['camp_name'] = _camp_name
		myjson_line['repeat_id'] = str(self.cnt_repet)
		myjson_line['exp_id'] = str(self.cnt_exp)
		myjson_line['timestamp'] = self.helper.get_str_timestamp()

		if _protocol in ['TCP','All']:

			# TCP downlink
			data = self.get_iperf_stats(server_ip=_server_ip, port=gparams._PORT_SERVER_IPERF,
			                                      flag_udp=False,flag_downlink=True, duration=_duration_sec,
			                                      bitrate=None,pack_len=_payload_bytes)

			if data is not None:
				try:
					myjson_line['tcp_dl_retransmits'] = data['end']['sum_sent']['retransmits']
					myjson_line['tcp_dl_sent_bps'] = data['end']['sum_sent']['bits_per_second']
					myjson_line['tcp_dl_sent_bytes'] = data['end']['sum_sent']['bytes']
					myjson_line['tcp_dl_received_bps'] = data['end']['sum_received']['bits_per_second']
					myjson_line['tcp_dl_received_bytes'] = data['end']['sum_received']['bytes']
					print('(Backend) DBG: TCP downlink bps ' + str(myjson_line['tcp_dl_received_bps']))
				except Exception as ex:
					print('(Backend) ERROR: TCP downlink write ' + str(ex))

			# TCP uplink
			data = self.get_iperf_stats(server_ip=_server_ip, port=gparams._PORT_SERVER_IPERF,
			                                      flag_udp=False,flag_downlink=False, duration=_duration_sec,
			                                      bitrate=None,pack_len=_payload_bytes)

			if data is not None:
				try:
					myjson_line['tcp_ul_retransmits'] = data['end']['sum_sent']['retransmits']
					myjson_line['tcp_ul_sent_bps'] = data['end']['sum_sent']['bits_per_second']
					myjson_line['tcp_ul_sent_bytes'] = data['end']['sum_sent']['bytes']
					myjson_line['tcp_ul_received_bps'] = data['end']['sum_received']['bits_per_second']
					myjson_line['tcp_ul_received_bytes'] = data['end']['sum_received']['bytes']
					print('(Backend) DBG: TCP uplink bps ' + str(myjson_line['tcp_ul_received_bps']))
				except Exception as ex:
					print('(Backend) ERROR: TCP uplink write ' + str(ex))

		if _protocol in ['UDP','All']:
			_bitrate=str(_target_rate_mbps)+'M'

			# UDP downlink
			data = self.get_iperf_stats(server_ip=_server_ip, port=gparams._PORT_SERVER_IPERF,
			                                      flag_udp=True,flag_downlink=True, duration=_duration_sec,
			                                      bitrate=_bitrate,pack_len=_payload_bytes)

			if data is not None:
				try:
					myjson_line['udp_dl_bytes'] = data['end']['sum']['bytes']
					myjson_line['udp_dl_bps'] = data['end']['sum']['bits_per_second']
					myjson_line['udp_dl_jitter_ms'] = data['end']['sum']['jitter_ms']
					myjson_line['udp_dl_lost_percent'] = data['end']['sum']['lost_percent']
					print('(Backend) DBG: UDP downlink bps ' + str(myjson_line['udp_dl_bps']))
				except Exception as ex:
					print('(Backend) ERROR: UDP downlink write ' + str(ex))

			# UDP uplink
			data = self.get_iperf_stats(server_ip=_server_ip, port=gparams._PORT_SERVER_IPERF,
			                                      flag_udp=True,flag_downlink=False, duration=_duration_sec,
			                                      bitrate=_bitrate,pack_len=_payload_bytes)

			if data is not None:
				try:
					myjson_line['udp_ul_bytes'] = data['end']['sum']['bytes']
					myjson_line['udp_ul_bps'] = data['end']['sum']['bits_per_second']
					myjson_line['udp_ul_jitter_ms'] = data['end']['sum']['jitter_ms']
					myjson_line['udp_ul_lost_percent'] = data['end']['sum']['lost_percent']
					print('(Backend) DBG: UDP uplink bps ' + str(myjson_line['udp_ul_bps']))
				except Exception as ex:
					print('(Backend) ERROR: UDP uplink write ' + str(ex))

		self.helper.write_dict2json(loc=gparams._RES_FILE_LOC_IPERF, mydict=myjson_line, clean=False)

	def get_iperf_stats(self,server_ip,port=5201,flag_udp=False,flag_downlink=False,duration=10,bitrate=None,
	                    pack_len=None):
		print('(Backend) DBG: Entered iperf3 stats at:'+str(self.helper.get_str_timestamp()))
		print('(Backend) DBG: Settings: UDP='+str(flag_udp)+
		      ',Downlink='+str(flag_downlink)+
		      ',bitrate='+str(bitrate)+
		      ',duration='+str(duration)+
			  ',pack_len='+str(pack_len)+
		      '...')
		# init iperf3
		cmd=['iperf3']

		# add server IP
		cmd.append('--client')
		cmd.append(str(server_ip))

		# add server port
		cmd.append('--port')
		cmd.append(str(port))

		# duration in sec
		cmd.append('--time')
		cmd.append(str(duration))

		# bitrate in bps
		if bitrate is not None:
			cmd.append('--bitrate')
			cmd.append(str(bitrate))

		# check if reverse (uplink if the default in iperf, from client to server)
		if flag_downlink:
			cmd.append('--reverse')

		# check if udp, default is tcp
		if flag_udp:
			cmd.append('--udp')

		if pack_len is not None:
			cmd.append('--length')
			cmd.append(str(pack_len))

		cmd.append('--json')

		result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		output= result.stdout

		try:
			data = json.loads(output)
			return data
		except Exception as ex:
			print('(Monitor) ERROR in iperf3 output json='+str(ex))
			return None


	def get_icmp(self):
		try:
			_enable=self.db_in_user['Experiment']['Baseline']['icmp']['enable']
			_payload_bytes = int(self.db_in_user['Experiment']['Baseline']['icmp']['payload (bytes)'])
			_interval_ms=int(self.db_in_user['Experiment']['Baseline']['icmp']['interval (ms)'])
			_packets=int(self.db_in_user['Experiment']['Baseline']['icmp']['packets'])
			_server_ip=self.db_in_user['Network']['Server IP']
			_camp_name=self.db_in_user['Measurement']['Campaign name']

			if _enable=='False':
				print('(Backend) DBG: ICMP ping test deactivated')
				return None
			else:
				print('(Backend) DBG: Init ICMP ping test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init ICMP ping: '+str(ex))
			return None



		myjson_line = gparams._RES_FILE_FIELDS_ICMP
		myjson_line['camp_name'] = _camp_name
		myjson_line['repeat_id'] = str(self.cnt_repet)
		myjson_line['exp_id'] = str(self.cnt_exp)
		myjson_line['timestamp'] = self.helper.get_str_timestamp()

		_interval_sec=_interval_ms*1e-3
		data = self.get_icmp_stats(server_ip=_server_ip,packs=_packets,
		                           interval_sec=_interval_sec,payload_bytes=_payload_bytes)

		if data is not None:
			try:
				myjson_line['min_rtt_ms'] = data.min_rtt
				myjson_line['avg_rtt_ms'] = data.avg_rtt
				myjson_line['max_rtt_ms'] = data.max_rtt
				myjson_line['rtts_ms']=data.rtts
				myjson_line['packets_sent'] = data.packets_sent
				myjson_line['packets_received'] = data.packets_received
				myjson_line['packet_loss_0to1'] = data.packet_loss
				myjson_line['jitter_ms'] = data.jitter
			except Exception as ex:
				print('(Backend) ERROR: ICMP ping write=' + str(ex))

		self.helper.write_dict2json(loc=gparams._RES_FILE_LOC_ICMP, mydict=myjson_line, clean=False)

	def get_icmp_stats(self,server_ip,packs=50,interval_sec=1,payload_bytes=64):
		print('(Monitor) DBG: Entered ICMP ping stats at:' + str(self.helper.get_str_timestamp()))
		print('(Monitor) DBG: Settings: server_ip=' + str(server_ip) + ',num_packets=' + str(packs) +
			  ',interval_sec=' + str(interval_sec) + ',payload_bytes='+str(payload_bytes)+' ...')

		try:
			# ping has a max packet len around 1500 bytes
			res = ping(server_ip, count=packs, interval=interval_sec,payload_size=payload_bytes,privileged=False,timeout=0.5)
			print('(Monitor) DBG: Ping res=' + str(res))

			if res.is_alive:
				print('(Monitor) DBG: Ping alive!')
				return res
			else:
				print('(Monitor) DBG: Ping NOT alive!')
				return None

		except Exception as ex:
			print('(Monitor) ERROR: Ping failed=' + str(ex))
			return None

	def get_udpping(self):
		try:
			_enable=self.db_in_user['Experiment']['Baseline']['icmp']['enable']
			_payload_bytes = int(self.db_in_user['Experiment']['Baseline']['icmp']['payload (bytes)'])
			_interval_ms=int(self.db_in_user['Experiment']['Baseline']['icmp']['interval (ms)'])
			_packets=int(self.db_in_user['Experiment']['Baseline']['icmp']['packets'])
			_server_ip=self.db_in_user['Network']['Server IP']
			_camp_name=self.db_in_user['Measurement']['Campaign name']

			if _enable=='False':
				print('(Backend) DBG: UDP ping test deactivated')
				return None
			else:
				print('(Backend) DBG: Init UDP ping test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init UDP ping: '+str(ex))
			return None



		myjson_line = gparams._RES_FILE_FIELDS_UDPPING
		data_df = self.get_udpping_stats(server_ip=_server_ip,payload_bytes=_payload_bytes,
		                                 packs=_packets,interval_ms=_interval_ms)

		if data_df is not None:
			try:
				data_df['camp_name'] = _camp_name
				data_df['repeat_id'] = str(self.cnt_repet)
				data_df['exp_id'] = str(self.cnt_exp)
				data_df['timestamp'] = self.helper.get_str_timestamp()

				with open(gparams._RES_FILE_LOC_UDPPING, 'a') as f:
					data_df.to_json(f, orient='records', lines=True)
				
			except Exception as ex:
				print('(Backend) ERROR: UDP ping write=' + str(ex))

	def get_udpping_stats(self,server_ip,payload_bytes=1250,packs=5000,interval_ms=20,port=1234):
		print('(Monitor) DBG: Entered udpPing at:'+str(self.helper.get_str_timestamp()))
		print('(Monitor) DBG: Settings: payload_bytes='+str(payload_bytes)+',packs='+str(packs)+
			  ',interval_ms='+str(interval_ms)+'...')
		# get loc
		try:
			mypath=gparams._UDPPING_ROOT
			cmd=[]
			#cmd.append(str(mypath))
			#cmd.append('&&')
			cmd.append('./udpClient')

			# add server IP
			cmd.append('-a')
			cmd.append(str(server_ip))

			# add packet size
			cmd.append('-s')
			cmd.append(str(payload_bytes))

			# num_packets
			cmd.append('-n')
			cmd.append(str(packs))

			# interval_ms
			cmd.append('-i')
			cmd.append(str(interval_ms))

			out = subprocess.check_output(cmd,cwd=mypath)

			my_strs = (str(out)).split('(all times in ns)')
			temp_str = my_strs[1].split('out of')
			final_str = temp_str[0]
			final_str = final_str.replace('\\n', '$')
			final_str = final_str.replace('\n', '$')
			final_str = final_str.replace('$', '\n')
			df_str = StringIO(final_str)

			df = pd.read_table(df_str, sep=gparams._UDPPING_DELIMITER, header=None)
			df.columns = gparams._RES_FILE_FIELDS_UDPPING

			temp_df=df.head(1)
			print('(Backend) Result=' + str(temp_df))

			return df
		except Exception as ex:
			print('(Backend) ERROR cannot process udpPing='+str(ex))
			return None

	def get_owamp(self):
		try:
			_enable=self.db_in_user['Experiment']['Baseline']['wamp']['enable']
			_payload_bytes = int(self.db_in_user['Experiment']['Baseline']['wamp']['payload (bytes)'])
			_interval_ms=int(self.db_in_user['Experiment']['Baseline']['wamp']['interval (ms)'])
			_packets=int(self.db_in_user['Experiment']['Baseline']['wamp']['packets'])
			_server_ip=self.db_in_user['Network']['Server IP']
			_camp_name=self.db_in_user['Measurement']['Campaign name']

			if _enable=='False':
				print('(Backend) DBG: OWAMP test deactivated')
				return None
			else:
				print('(Backend) DBG: Init OWAMP test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init OWAMP: '+str(ex))
			return None


		myjson_line = gparams._RES_FILE_FIELDS_OWAMP
		data_df = self.get_owamp_stats(server_ip=_server_ip,payload_bytes=_payload_bytes,
		                                 packs=_packets,interval_ms=_interval_ms)

		if data_df is not None:
			try:
				data_df['camp_name'] = _camp_name
				data_df['repeat_id'] = str(self.cnt_repet)
				data_df['exp_id'] = str(self.cnt_exp)
				data_df['timestamp'] = self.helper.get_str_timestamp()

				with open(gparams._RES_FILE_LOC_OWAMP, 'a') as f:
					data_df.to_json(f, orient='records', lines=True)				
				
			except Exception as ex:
				print('(Backend) ERROR: OWAMP write=' + str(ex))

	def get_owamp_stats(self,server_ip,payload_bytes=1250,packs=5000,interval_ms=20):
		print('(Monitor) DBG: Entered OWAMP at:'+str(self.helper.get_str_timestamp()))
		print('(Monitor) DBG: Settings: payload_bytes='+str(payload_bytes)+',packs='+str(packs)+
			  ',interval_ms='+str(interval_ms)+'...')
		# get loc
		try:
			cmd = ['owping']

			cmd.append('-c')
			cmd.append(str(packs))

			cmd.append('-s')
			cmd.append(str(payload_bytes))

			interval_sec=interval_ms*1e-3
			cmd.append('-i')
			cmd.append(str(interval_sec))

			cmd.append('-R')

			cmd.append(str(server_ip))

			result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			output = result.stdout

			output = output.replace(' ', gparams._OWAMP_DELIMITER)
			output = output.replace('\n', '$')
			output = output.replace('$', '\n')
			df_str = StringIO(output)

			df = pd.read_table(df_str, sep=gparams._OWAMP_DELIMITER, header=None)
			df.columns = gparams._RES_FILE_FIELDS_OWAMP

			df['is_previous_larger'] = (df[gparams._KEY_WORD_OWAMP].shift(1) > df[gparams._KEY_WORD_OWAMP]).astype(int)
			mylist = df.index[df['is_previous_larger'] == 1].tolist()
			df = df.drop('is_previous_larger', axis=1)
			sep_raw = mylist[0]

			df.loc[:sep_raw, 'direction'] = 'ul'
			df.loc[sep_raw:, 'direction'] = 'dl'
			print('(Backend) DBG OWAMP tx sync status='+str(df[gparams._DBG_KEY_WORD_OWAMP].mean()))
			return df
		except Exception as ex:
			print('(Backend) ERROR cannot process OWAMP='+str(ex))
			return None

	def get_twamp(self):
		try:
			_enable=self.db_in_user['Experiment']['Baseline']['wamp']['enable']
			_payload_bytes = int(self.db_in_user['Experiment']['Baseline']['wamp']['payload (bytes)'])
			_interval_ms=int(self.db_in_user['Experiment']['Baseline']['wamp']['interval (ms)'])
			_packets=int(self.db_in_user['Experiment']['Baseline']['wamp']['packets'])
			_server_ip=self.db_in_user['Network']['Server IP']
			_camp_name=self.db_in_user['Measurement']['Campaign name']

			if _enable=='False':
				print('(Backend) DBG: TWAMP test deactivated')
				return None
			else:
				print('(Backend) DBG: Init TWAMP test ................')
		except Exception as ex:
			print('(Backend) ERROR: Init TWAMP: '+str(ex))
			return None


		myjson_line = gparams._RES_FILE_FIELDS_TWAMP
		data_df = self.get_twamp_stats(server_ip=_server_ip,payload_bytes=_payload_bytes,
		                                 packs=_packets,interval_ms=_interval_ms)

		if data_df is not None:
			try:
				data_df['camp_name'] = _camp_name
				data_df['repeat_id'] = str(self.cnt_repet)
				data_df['exp_id'] = str(self.cnt_exp)
				data_df['timestamp'] = self.helper.get_str_timestamp()

				with open(gparams._RES_FILE_LOC_TWAMP, 'a') as f:
					data_df.to_json(f, orient='records', lines=True)				
								
			except Exception as ex:
				print('(Backend) ERROR: OWAMP write=' + str(ex))

	def get_twamp_stats(self,server_ip,payload_bytes=1250,packs=5000,interval_ms=20):
		print('(Monitor) DBG: Entered TWAMP at:'+str(self.helper.get_str_timestamp()))
		print('(Monitor) DBG: Settings: payload_bytes='+str(payload_bytes)+',packs='+str(packs)+
			  ',interval_ms='+str(interval_ms)+'...')
		# get loc
		try:
			cmd = ['twping']

			cmd.append('-c')
			cmd.append(str(packs))

			cmd.append('-s')
			cmd.append(str(payload_bytes))

			interval_sec=interval_ms*1e-3
			cmd.append('-i')
			cmd.append(str(interval_sec))

			cmd.append('-R')

			cmd.append(str(server_ip))

			result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			output = result.stdout

			output = output.replace(' ', gparams._TWAMP_DELIMITER)
			output = output.replace('\n', '$')
			output = output.replace('$', '\n')
			df_str = StringIO(output)

			df = pd.read_table(df_str, sep=gparams._TWAMP_DELIMITER, header=None)
			df.columns = gparams._RES_FILE_FIELDS_TWAMP
			print('(Backend) DBG OWAMP tx sync status='+str(df[gparams._DBG_KEY_WORD_OWAMP].mean()))
			return df
		except Exception as ex:
			print('(Monitor) ERROR cannot process TWAMP='+str(ex))
			return None

	def get_baseline_measurements(self):
		self.get_iperf()
		self.get_icmp()
		self.get_udpping()
		self.get_owamp()
		self.get_twamp()


if __name__ == '__main__':
	print('(Backend) DBG: Backend initialized')
	pd.options.mode.chained_assignment = None  # default='warn'
	backend=Backend()
