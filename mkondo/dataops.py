import datetime
import os
import json
import gzip

from abc import ABCMeta, abstractmethod

class TweetParser:
	""" This is intended as an abstract base class for parsing the Tweet files based on
	mkondo's format for writing out tweet data. """

	__metaclass__ = ABCMeta

	def read_tweet_line(self, line):
		date = line.split('|', 1)[0]
		json_text = line.split('|', 1)[1]
		tweet_json = json.loads(json_text)
		return (date, tweet_json)

	@abstractmethod
	def parse_line(self, line, **kwargs):
		""" Process a single tweet line. """
		
	def parse_file(self, filename, **kwargs):
		if 'gz' in filename:
			f = gzip.open(filename, 'r')
			for line in f:
				if len(line) > 2:
					self.parse_line(line, **kwargs)

class TweetsAnalyzer:
	def __init__(self):
		self.number_of_tweets = 0

	def process_line(self, line):
		json_tweet = line.split('|', 1)[1]
		rt = json.loads(json_tweet)
		if rt['text'] is not None:
			self.number_of_tweets += 1

	def analyze_file(self, filename):
		if 'gz' in filename:
			f = gzip.open(filename, 'r')
			for line in f:
				if len(line) > 2:
					self.process_line(line)

	def analyze_file_uncompressed(self, filename):
		f = open(filename, 'r')
		for line in f:
			if len(line) > 2:
				self.process_line(line)

	def export_data(self):
		return json.dumps({'tweet_count':self.number_of_tweets})

class LocationAnalyzer(TweetsAnalyzer):

	def __init__(self):
		TweetsAnalyzer.__init__(self)
		self.tweeters = {}
		self.num_with_precise_geolocation = 1
		self.place_type_counts = {}

	def increment_place_type_counts(self, place_type):
		if place_type in self.place_type_counts:
			self.place_type_counts[place_type] += 1
		else:
			self.place_type_counts[place_type] = 1

	def increment_tweeter_frequency(self, twitter_user_id):
		if twitter_user_id in self.tweeters:
			self.tweeters[twitter_user_id] += 1
		else:
			self.tweeters[twitter_user_id] = 1

	def process_line(self, line):	
		TweetsAnalyzer.process_line(self, line)

		json_tweet = line.split('|', 1)[1]
		rt = json.loads(json_tweet)
		if rt['text'] is not None:
			if rt['coordinates'] is not None:
				self.num_with_precise_geolocation += 1
			if rt['user']['id'] is not None:
				self.increment_tweeter_frequency(rt['user']['id'])
			if rt['coordinates'] is None:
				self.increment_place_type_counts(rt['place']['place_type'])

	def export_data(self):
		return json.dumps({'tweet_count':self.number_of_tweets,
			'precise_coordinates_count':self.num_with_precise_geolocation,
			'place_type_counts':self.place_type_counts,
			})

def get_directory_file_list(datadir):
	""" For a particular path, get a list of directories and files (but only include 
	gzip'd files."""
	directory_listing = os.listdir(datadir)

	#separate directories, and data files

	directories = []
	data_files = []
	for d in directory_listing:
		if os.path.isdir(os.path.join(datadir, d)):
			directories.append(d)
		elif ('gz' in d) or ('log' in d and len(d.split('.')) > 2):
			#If we're picking up uncompressed files, we only want the ones that have been 
			#rotated. Hence the checking for an extra dot in the file name. 
			data_files.append(d)

	return (directories, data_files)

def get_all_directory_file_list(datadir):
	""" For a particular path, get a list of directories, and *all* files."""
	directory_listing = os.listdir(datadir)

	#separate directories, and data files
	directories = []
	data_files = []
	for d in directory_listing:
		if os.path.isdir(d):
			directories.append(d)
		else:
			data_files.append(d)
	return (directories, data_files)

def today():
	return datetime.datetime.today().strftime("%Y%m%d")

def today_hyphenated():
	return datetime.datetime.today().strftime("%Y-%m-%d")

def yesterday():
	return (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")

def hours_from_file_list(data_files):
	hours = []
	for d in data_files:
		h = d.split('.')[2]
		hours.append(h)
	hours.sort()
	return hours

def pretty_print_dictionary(dictionary):
	for key in sorted(dictionary.keys()):
		output = "%s,%s" % (key, dictionary[key])
		print output
