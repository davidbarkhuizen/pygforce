import random

import networkx as nx

import gobject
import gtk

from force_directed_graph import ForceDirectedGraph, Tag
from graphical_event_manager import GEM

CANVAS_WIDTH = 100
CANVAS_HEIGHT = (100.0 / 1.6) * 1

def gen_xy():
    x = (- float(CANVAS_WIDTH) / 2.0) +  (random.random() * float(CANVAS_WIDTH))
    y = (- float(CANVAS_HEIGHT) / 2.0) + (random.random() * float(CANVAS_HEIGHT))
    return (x,y)


def generate_graph():
    
    g = nx.Graph()
	
	# minimal_connected_3
#    x,y = gen_xy()
#    A = Tag(x, y, '')
#    g.add_node(A)
#    
#    for i in range(7):
#        (x,y) = gen_xy()
#        tag = Tag(x, y, '')
#        g.add_node(tag)
#   

    p = 11
    max_degree = 2
    
    nodes = []
    
    for i in range(p):
        (x,y) = gen_xy()
        tag = Tag(x, y, '')
        g.add_node(tag)
        nodes.append(tag)
    
    for i in range(p):
        node = nodes[i]
        
        used_neighbours = []
        for j in range(random.randint(1, max_degree)):
        
            got_number = False
            while got_number == False:
                z = random.randint(0, len(nodes) - 1)
                if nodes[z] != node:
                    if nodes[z] not in used_neighbours:
                        g.add_edge(node, nodes[z])
                        got_number = True
    
#    (x,y) = gen_xy()
#    B = Tag(x, y, '')
#    g.add_node(B)
#    
#    g.add_edge(A, B)
#    
#    for node in [A, B]:
#    	for i in range(2):
#    		(x,y) = gen_xy()
#    		tag = Tag(x, y, '')
#    		g.add_node(tag)
#    		g.add_edge(node, tag)
    
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
	tick_event_period = 50
	
	# attach tick event handler
	gem.timer = gobject.timeout_add(tick_event_period, gem.time_tick_handler)
	
	# launch GTK
	gtk.main()

if __name__ == '__main__':
	main()