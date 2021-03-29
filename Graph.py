import json
import cv2
import numpy as np
from collections import defaultdict

from Node_Person import Person
from suren.util import eprint, stop, progress, Json


try:
	# import networkx as nx
	import matplotlib.pyplot as plt
	import matplotlib.cm as cm

except ImportError as e:
	print(e)


# SHOW = False  # No idea if this would work when importing @all...maybe call as function?


# Graph visualization packages

class Graph:
	def __init__(self, time_series_length=None, save_name=None):
		"""
		:param timeSeriesLength: Number of frames
		"""
		self.time_series_length = time_series_length

		self.n_nodes = 0
		self.n_person = 0
		self.nodes = []
		self.saveGraphFileName = save_name

		self.BIG_BANG = 0  # HUH -_-

	@staticmethod
	def plot_import():
		try:
			# import networkx
			import matplotlib.pyplot

			return None
		except ImportError as e:
			print(e)
			# SHOW = False  # No idea if this would work when importing @all...maybe call as function?
			return e

	def __repr__(self):
		return "Graph with %d nodes" % self.n_nodes

	def get_plot_points(self):
		sc_x = []
		sc_y = []
		lines = []

		for t in range(self.time_series_length):
			# pos = {}
			sc_tx, sc_ty = [], []
			line_t = defaultdict(list)
			for n, p in enumerate(self.nodes):
				# print(n, p.params)
				# if p.params["detection"][t]:
				p_x1 = p.params["xMin"][t]
				p_y1 = p.params["yMin"][t]
				p_x2 = p.params["xMax"][t]
				p_y2 = p.params["yMax"][t]
				p_x = (p_x1 + p_x2) / 2
				p_y = (p_y1 + p_y2) / 2
				# pos[n] = (p_x, p_y)
				sc_tx.append(p_x)
				sc_ty.append(p_y)

				if p.params["handshake"][t]['person'] is not None:
					n1, n2 = sorted([n, p.params["handshake"][t]['person']])
					line_t["%d_%d"%(n1, n2)].append([p_x, p_y])

			sc_x.append(sc_tx)
			sc_y.append(sc_ty)

			# @suren : find a better way to implement variable size array
			try: line_t = np.array([line_t[l] for l in line_t]).transpose((0, 2, 1))
			except ValueError: line_t = []

			lines.append(line_t)

		sc_x = np.array(sc_x).transpose()
		sc_y = np.array(sc_y).transpose()
		# lines = np.array(lines)			# lines is a variable size array

		return sc_x, sc_y, lines

	def get_cmap(self, show=False):
		colors = cm.hsv(np.linspace(0, .8, self.n_nodes))
		window = 10

		col_arr = np.ones((window, 4))

		col_arr[:, -1] = np.power(.8, np.arange(window))[::-1]

		arr1 = np.tile(colors, (window, 1, 1)).transpose((1, 0, 2))
		# print(colors.shape, arr1.shape)
		arr2 = np.tile(col_arr, (self.n_nodes, 1, 1))
		# print(col_arr.shape, arr2.shape)

		cmap = arr1 * arr2

		# print(arr1[1, :, :], arr2[1, :, :])

		# print(colors)

		# stop()
		if show:
			x = np.tile(np.arange(cmap.shape[0]), (cmap.shape[1], 1))
			y = np.tile(np.arange(cmap.shape[1]), (cmap.shape[0], 1)).transpose()
			# print(x)
			# print(y)
			plt.figure()
			plt.title("Colour map (Close to continue)")
			plt.scatter(x.flatten(), y.flatten(), color=np.reshape(cmap, (-1, 4), order='F'))
			plt.show()

		return cmap

	def plot(self, window=10, show_cmap=True):

		if Graph.plot_import() is not None:
			eprint("Package not installed", Graph.plot_import())
			return

		# plt.figure()

		cmap = self.get_cmap(show=show_cmap)

		sc_x, sc_y, lines = self.get_plot_points()

		print(sc_x.shape, sc_y.shape, cmap.shape)

		# PLOT
		ylim = [np.min(sc_y, axis=None)-5, np.max(sc_y, axis=None)+5]
		xlim = [np.min(sc_x, axis=None)-5, np.max(sc_x, axis=None)+5]

		fig = plt.figure()
		plt.xlim(xlim[0], xlim[1])
		plt.ylim(ylim[0], ylim[1])
		ax = plt.gca()
		# plt.xlim((np.min(sc_x, axis=None))

		plt.ion()

		for t in range(self.time_series_length):
			sc_x_ = sc_x[:, max(t + 1 - window, 0):t + 1]
			sc_y_ = sc_y[:, max(t + 1 - window, 0):t + 1]
			cmap_ = cmap[:, max(0, window - (t + 1)):, :]

			# print(sc_x_)
			# print(sc_y_)
			# print(cmap_)

			# print(sc_x_.shape, sc_y_.shape, cmap_.shape)

			ax.scatter(sc_x_.flatten(), sc_y_.flatten(), color=np.reshape(cmap_, (-1, 4), order='C'))

			for l in lines[t]:
				ax.plot(l[0], l[1])
				plt.pause(.5)


			else:
				plt.pause(.1)

			ax.clear()
			ax.set_xlim(xlim[0], xlim[1])
			ax.set_ylim(ylim[0], ylim[1])

			if (t + 1) % 20 == 0:
				progress(t + 1, self.time_series_length, "drawing graph")


	# plt.show(block=True)

	def get_nxt_id(self):
		return len(self.nodes)

	def add_person(self, p=None):
		# @SUREN what is fed in as p here?
		p = Person(time_series_length=self.time_series_length, idx=self.get_nxt_id()) if p is None else p

		self.nodes.append(p)
		self.n_person += 1
		self.n_nodes = len(self.nodes)

		return p

	# def addNode(self,time):
	# 	print("GRAPH: adding (person) node")
	# 	self.nodes.append(Person())
	# 	return len(self.nodes)-1

	# def addNode2(self,node):
	# 	'''
	# 	Merge this with addNode()
	# 	'''
	# 	print("GRAPH: adding (general) node")
	# 	self.nodes.append(node)
	# 	return len(self.nodes)-1

	def getNode(self, idx):
		return self.nodes[idx]

	def make_jsonable(self, data):
		for node in data["nodes"]:
			for param in node:
				print(param, node[param])
				if param == "handshake":
					for t in range(self.time_series_length):
						print(type(node[param][t]['person']))
						print(type(node[param][t]['confidence']))

				else:
					for t in range(self.time_series_length):
						print(type(node[param][t]))
					# print(type(node["handshake"]))

	def saveToFile(self, file_name=None):
		if file_name is None: file_name = self.saveGraphFileName

		data = {"N": len(self.nodes), "frames": self.time_series_length, "nodes": []}
		for n in self.nodes:
			data["nodes"].append(n.getParamsDict())

		# self.make_jsonable(data)

		js = Json(file_name)
		js.write(data)

		# with open(file_name, 'w') as outfile:
		# 	json.dump(data, outfile)
		print("Finished writing all nodes to {}".format(file_name))

	def init_from_json(self, file_name):
		with open(file_name) as json_file:
			data = json.load(json_file)

		try:
			N = data["N"]
			assert len(data["nodes"]) == N, "No of nodes not equal to N"
		except Exception as e:
			eprint(e)
			N = len(data["nodes"])

		try:
			time_series_length = data["frames"]
			assert len(data["nodes"][0]["detection"]) == time_series_length, "No of nodes not equal to N"
		except Exception as e:
			eprint(e)
			time_series_length = len(data["nodes"][0]["detection"])

		if N == 0:
			eprint("No nodes :(")
			return

		if self.time_series_length is None: self.time_series_length = time_series_length


		for n in range(N):
			p = self.add_person()
			p.setParamsFromDict(data["nodes"][n])

	def calculate_standing_locations(self):
		for n in self.nodes:
			n.calculate_standing_locations()

	def interpolate_undetected_timestamps(self):
		for n in self.nodes:
			n.interpolate_undetected_timestamps()

if __name__ == "__main__":
	g = Graph()
	# g.init_from_json('./data/vid-01-graph.json')		# Start from yolo
	g.init_from_json('./data/vid-01-graph_handshake.json')	# Start from handshake

	print("Created graph with nodes = %d for frames = %d. Param example:" % (g.n_nodes, g.time_series_length))
	print(g.nodes[0].params)

	g.plot()
