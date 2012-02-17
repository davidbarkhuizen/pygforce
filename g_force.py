import random

import networkx as nx

import gobject
import gtk

from force_directed_graph import ForceDirectedGraph
from graphical_event_manager import GEM

CANVAS_WIDTH = 100
CANVAS_HEIGHT = (100.0 / 1.6) * 1

class Tag(object):

	last_used_idx = 0
	@classmethod
	def pop_unused_idx(cls):
		new_idx = cls.last_used_idx + 1
		cls.last_used_idx = new_idx
		return new_idx		
	
	def __init__(self, x, y, label):
	
		self.idx = Tag.pop_unused_idx()
		
		self.x = x
		self.y = y
		
		self.label = label
		
		self.net_electrostatic_force = (0, 0)
		self.net_spring_force = (0, 0)
		self.displacement = (0, 0)

	def __str__(self):
		
		s = ('%i = %s' % (self.idx, self.label)) + '\n'
		s = s + ('(x,y) = (%f,%f)' % (self.x, self.y)) + '\n'
		
		(Fx, Fy) = self.net_electrostatic_force
		s = s + ('electro-static Fx, Fy = %f, %f' % (Fx, Fy)) + '\n'
		
		(Fx, Fy) = self.net_spring_force
		s = s + ('spring Fx, Fy = %f, %f' % (Fx, Fy)) + '\n'	

		(dx, dy) = self.displacement
		s = s + ('displacement dx, dy = %f, %f' % (dx, dy)) + '\n'		
		
		return s

def generate_graph():
	g = nx.Graph()
	
	# minimal_connected_3
	
	def gen_xy():
		x = (- float(CANVAS_WIDTH) / 2.0) +  (random.random() * float(CANVAS_WIDTH))
		y = (- float(CANVAS_HEIGHT) / 2.0) + (random.random() * float(CANVAS_HEIGHT))
		return (x,y)
	
	(x,y) = gen_xy()
	A = Tag(x, y, '')
	g.add_node(A)

	(x,y) = gen_xy()
	B = Tag(x, y, '')
	g.add_node(B)

	g.add_edge(A, B)
	
	for node in [A, B]:
		for i in range(2):
			(x,y) = gen_xy()
			tag = Tag(x, y, '')
			g.add_node(tag)
			g.add_edge(node, tag)
				
	return g

def main():
	'''
	generate graph, set time, and launch gtk via gtk.main()
	'''
	# construct test graph
	g = generate_graph()
	
	# launch graphical event manager
	gem = GEM(graph=g)
	
	# tick event period
	tick_event_period = 10
	
	# attach tick event handler
	gem.timer = gobject.timeout_add(tick_event_period, gem.time_tick_handler)
	
	# launch GTK
	gtk.main()

if __name__ == '__main__':
	main()