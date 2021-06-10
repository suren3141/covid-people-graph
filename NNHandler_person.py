import argparse
import json
import numpy as np
import os, sys
import matplotlib.pyplot as plt
from collections import defaultdict

from NNHandler_yolo import NNHandler_yolo
from NNHandler_image import NNHandler_image, cv2

from Node_Person import Person

from suren.util import Json, eprint

# This is only needed if running YOLO / deepsort
# Not needed if the values are loaded from file
try:
	import tensorflow as tf
	from tensorflow.python.saved_model import tag_constants

	sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/submodules/yolov4-deepsort")
	print(sys.path)

	from deep_sort import preprocessing, nn_matching
	from deep_sort.detection import Detection
	from deep_sort.tracker import Tracker
	from tools import generate_detections as gdet
	import core.utils as utils
	# from core.yolov4 import filter_boxes
	from tensorflow.python.saved_model import tag_constants

	from core.config import cfg
except Exception as e:
	eprint("Cannot run YOLO:", e)


class NNHandler_person(NNHandler_yolo):
	yolo_dir = "./suren/temp/yolov4-deepsort-master/"
	model_filename = yolo_dir + 'model_data/mars-small128.pb'
	weigths_filename = yolo_dir + '/checkpoints/yolov4-416'

	class_names = ["person"]

	# Definition of the parameters
	max_cosine_distance = 0.4
	nn_budget = None
	nms_max_overlap = 1.0

	iou_thresh = .45
	score_thresh = .5
	input_size = 416


	def __init__(self, json_file=None, is_tracked=True, vis=True, verbose=True, debug=False):

		super().__init__(json_file=json_file, is_tracked=is_tracked, vis=vis, verbose=verbose, debug=debug)
		print("\t[*] Person detector")

	def extractValForKey(self,st,startSt,endSt):
		a=st.index(startSt)+len(startSt)
		b=st.index(endSt)
		return st[a:b].strip()

	def refinePersonTrajectory(self,p):
		# @ Is this function working?? getparam needs 2 arguments
		firstApperanceT=0
		lastAppearanceT=p.timeSeriesLength-1

		for a in range(p.timeSeriesLength):
			if p.getParam("detection")==False:
				firstApperanceT=a

		for a in range(p.timeSeriesLength-1,-1,-1):
			if p.getParam("detection")==False:
				lastAppearanceT=a			


		print("This person is visible only from {} to {} frames".format(firstApperanceT,lastAppearanceT))

	def update_graph_nodes(self):
		graph = self.graph

		if graph.time_series_length is None: graph.time_series_length = self.time_series_length
		else: raise Exception("Graph is not empty")

		assert len(graph.nodes) == 0, "Graph not empty. Cannot update non-empty graph"

		person_dic = defaultdict(dict)

		for t in range(self.time_series_length):
			try: yolo_bbox = self.json_data[t]
			except: yolo_bbox = self.json_data[str(t)]		# If reading from json file

			for bbox in yolo_bbox:
				idx = bbox.pop("id")
				person_dic[idx][t] = bbox

		unclassified = person_dic.pop(-1)

		# print(person_dic)

		for idx in person_dic:
			detected = [True if t in person_dic[idx] else False for t in range(self.time_series_length)]

			x_min = [person_dic[idx][t]["x1"] if detected[t] else 0 for t in range(self.time_series_length)]
			x_max = [person_dic[idx][t]["x2"] if detected[t] else 0 for t in range(self.time_series_length)]
			y_min = [person_dic[idx][t]["y1"] if detected[t] else 0 for t in range(self.time_series_length)]
			y_max = [person_dic[idx][t]["y2"] if detected[t] else 0 for t in range(self.time_series_length)]

			p = Person(time_series_length=self.time_series_length,
					   initParams={"xMin":x_min, "xMax":x_max, "yMin":y_min, "yMax":y_max, "detection":detected})
			# print(idx, p.params)
			graph.add_person(p)

		graph.state["people"] = 2


	def runForBatch(self):
		self.update_graph_nodes()




if __name__=="__main__":

	json_loc = "./data/labels/DEEE/yolo/cctv1-yolo.json"
	img_loc = "./data/videos/DEEE/cctv1.mp4"

	parser = argparse.ArgumentParser()

	parser.add_argument("--input_file", "-i", type=str, dest="input_file", default=img_loc)
	parser.add_argument("--output_file", "-o", type=str, dest="output_file", default=json_loc)
	parser.add_argument("--overwrite", "--ow", action="store_true", dest="overwrite")
	parser.add_argument("--visualize", "--vis", action="store_true", dest="visualize")
	parser.add_argument("--verbose", "--verb", action="store_true", dest="verbose")
	parser.add_argument("--tracked", "-t", type=bool, dest="tracked", default=True)

	args = parser.parse_args()
	# args.overwrite = True
	# args.verbose=True

	img_loc = args.input_file
	json_loc = args.output_file

	# TEST
	img_handle = NNHandler_image(format="avi", img_loc=img_loc)
	img_handle.runForBatch()

	nn_yolo = NNHandler_person(vis=args.visualize, is_tracked=args.tracked, verbose=args.verbose, debug=True)
	try:
		if os.path.exists(json_loc):
			if args.overwrite:
				raise Exception("Overwriting json : %s"%json_loc)

			# To load YOLO + DSORT track from json
			nn_yolo.init_from_json(json_loc)

		else:
			raise Exception("Json does not exists : %s"%json_loc)
	except:
		# To create YOLO + DSORT track and save to json
		nn_yolo.create_yolo(img_handle)
		nn_yolo.save_json(json_loc)

