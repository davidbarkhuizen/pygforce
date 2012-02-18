import random

import networkx as nx

import gobject
import gtk

from force_directed_graph import ForceDirectedGraph
from node_tag import Tag
from graphical_event_manager import GEM

CANVAS_WIDTH = 100
CANVAS_HEIGHT = (100.0 / 1.6) * 1

def gen_xy():
    x = (- float(CANVAS_WIDTH) / 2.0) +  (random.random() * float(CANVAS_WIDTH))
    y = (- float(CANVAS_HEIGHT) / 2.0) + (random.random() * float(CANVAS_HEIGHT))
    return (x,y)

def generate_graph(p=11, max_edges_to_create_per_node_per_pass=2):
    '''
    generate a semi-random graph of size p
    
    generate p vertices, with random x,y co-ords
    for each vertex:
      randomly add at most max_edges_to_create_per_node_per_pass new edges
    '''
    
    g = nx.Graph()	
    
    nodes = []
    
    for i in range(p):
        (x,y) = gen_xy()
        tag = Tag(x, y, '')
        g.add_node(tag)
        nodes.append(tag)
    
    for i in range(p):
        node = nodes[i]
        
        for j in range(random.randint(1, max_edges_to_create_per_node_per_pass)):
        
            new_edge_added = False
            while new_edge_added == False:
                z = random.randint(0, len(nodes) - 1)
                if nodes[z] != node:
                    if ((nodes[z], node) not in g.edges()) and ((node, nodes[z]) not in g.edges()):
                        g.add_edge(node, nodes[z])
                        new_edge_added = True
   
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