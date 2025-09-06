import gparams
import pandas as pd
import time
from time import mktime
from datetime import datetime
import random, string
import json
import os
from pathlib import Path

class Helper:

	def __init__(self):
		pass

	def write_db(self,loc,mystr):
		try:
			with open(loc, mode='a') as myfile:
				myfile.write(mystr+'\n')
				return 200
		except Exception as ex:
			print('(Helper) ERROR at DB write=' + str(ex))
			return None

	def clean_db(self,loc):
		try:
			open(loc, 'w').close()
			return 200
		except Exception as ex:
			print('(Helper) ERROR at DB clean='+str(ex))
			return None

	def init_db(self,loc,header=None):
		res=self.clean_db(loc=loc)

		if None not in (header, res):
			res=self.write_db(loc=loc,mystr=header)

		return res

	def read_db_df(self,loc):
		try:
			mydf=pd.read_csv(loc,delimiter=gparams._DELIMITER)
			return mydf
		except Exception as ex:
			print('(Helper) ERROR: During db read='+str(ex))
			return None

	def read_json2dict(self,loc):
		try:
			with open(loc, 'r') as openfile:
				json_object = json.load(openfile)
			return json_object
		except Exception as ex:
			print('(Helper) ERROR: During read_json2dict=' + str(ex))
			return None

	def read_jsonlines2pandas(self,loc):
		try:
			df = pd.read_json(loc, lines=True)
			return df
		except Exception as ex:
			print('(Helper) ERROR: During read_jsonlines2pandas=' + str(ex))
			return None

	def write_dict2json(self,loc,mydict,clean=True):
		try:
			# Serializing json
			json_object = json.dumps(mydict)

			# Writing to sample.json
			if clean:
				self.clean_db(loc=loc)

			with open(loc, 'a') as outfile:
				outfile.write(json_object+'\n')
			return 200
		except Exception as ex:
			print('(Helper) ERROR: During write_dict2json=' + str(ex))
			return None

	def write_df2db(self,loc,df,header=False):
		try:
			df.to_csv(loc, sep=gparams._DELIMITER, encoding='utf-8',index=False,header=header,mode='a')
			return 200
		except Exception as ex:
			print('(Helper) ERROR: During db write='+str(ex))
			return None

	def create_csv_line(self,list_of_str):
		final_str=''
		for mystr in list_of_str:
			final_str=final_str+str(mystr)+gparams._DELIMITER
		final_str = final_str[:-1]
		return final_str

	def wait(self,time_sec):
		time.sleep(time_sec)

	def get_curr_asctime(self):
		return time.asctime(time.localtime(time.time()))

	def diff_asctimes_sec(self,early,late):
		early = time.strptime(early)
		early = mktime(early)
		late = time.strptime(late)
		late = mktime(late)
		return late-early

	def get_str_timestamp(self):
		return str(datetime.now())

	def get_folderstr_timestamp(self):
		mybase=str(datetime.now())
		mybase,_=mybase.split('.')
		mybase = mybase.replace('-', '')
		mybase=mybase.replace(' ','')
		mybase = mybase.replace(':', '')
		mybase = mybase.replace('.', '')
		return mybase

	def get_rnd_str(self,str_len):
		letters = string.ascii_lowercase+string.digits
		return ''.join(random.choice(letters) for i in range(str_len))


	def merge_multiple_logs(self,input_folders,out):
		output_folder = Path(gparams._ROOT_DIR) / out
		output_folder.mkdir(parents=True, exist_ok=True)

		# Collect all files that exist in input folders
		all_files = {}
		for input_folder in input_folders:
			folder_path = Path(gparams._ROOT_DIR) / input_folder
			for file in folder_path.glob("*.json"):
				all_files.setdefault(file.name, []).append(file)

		# Merge each set of files
		for filename, paths in all_files.items():
			merged_lines = []
			for path in paths:
				with open(path) as f:
					merged_lines.extend(f.readlines())

			# sort by time key (safe in case logs overlap)
			try:
				merged_lines = sorted(
					merged_lines,
					key=lambda line: json.loads(line).get("time", "")
				)
			except Exception:
				# if parsing fails, just keep file order
				pass

			# write to new folder
			out_path = output_folder / filename
			with open(out_path, "w") as f:
				f.writelines(merged_lines)


def test1():
	my_in=[
		'extra_logs/01_db_ntw',
		 'extra_logs/02_db_ntw',
		 'extra_logs/03_db_ntw',
		 'extra_logs/04_db_ntw',
		 'extra_logs/05_db_ntw',
		'extra_logs/06_db_ntw',
		'extra_logs/07_db_ntw',
		'extra_logs/08_db_ntw',
		'extra_logs/09_db_ntw',
		'extra_logs/10_db_ntw',
		'extra_logs/11_db_ntw',
		 ]
	my_out='new_db'
	helper=Helper()
	helper.merge_multiple_logs(input_folders=my_in,out=my_out)

def test2():
	my_in=[
		'app_logs/01_db_app',
		 'app_logs/02_db_app',
		 'app_logs/03_db_app',
		 'app_logs/04_db_app',
		 'app_logs/05_db_app',
		'app_logs/06_db_app',
		'app_logs/07_db_app',
		'app_logs/08_db_app',
		'app_logs/09_db_app',
		'app_logs/10_db_app',
		'app_logs/11_db_app',
		 ]
	my_out='new_db'
	helper=Helper()
	helper.merge_multiple_logs(input_folders=my_in,out=my_out)

test2()