import networkx as nx
from random import random, randint
from node_tag import Tag

def construct_xy_factory(AREA_WIDTH, AREA_HEIGHT):
    
    used = []
    
    def gen_xy():
        unique = False        
        while not unique:
            x = (- float(AREA_WIDTH) / 2.0) +  (random() * float(AREA_WIDTH))
            y = (- float(AREA_HEIGHT) / 2.0) + (random() * float(AREA_HEIGHT))
            unique = (x,y) not in used
        used.append((x,y))
        return (x,y)

    return gen_xy

def generate_graph(area_width, area_height, p=11, max_edges_to_create_per_node_per_pass=2):
    '''
    generate a semi-random graph of size p
    
    generate p vertices, with random x,y co-ords
    for each vertex:
      randomly add at most max_edges_to_create_per_node_per_pass new edges
    '''
    
    g = nx.Graph()    
    
    f_gen_xy = construct_xy_factory(area_width, area_height)
    
    for i in range(p):
        (x,y) = f_gen_xy()
        tag = Tag(x, y, '')
        tag.label = 'Node %i' % tag.idx
        g.add_node(tag)    
    
    nodes = g.nodes()    
    
    for node in nodes:
        
        for j in range(randint(1, max_edges_to_create_per_node_per_pass)):
        
            new_edge_added = False
            while new_edge_added == False:
                
                z = randint(0, len(nodes) - 1)
                if nodes[z] != node:
                    if ((nodes[z], node) not in g.edges()) and ((node, nodes[z]) not in g.edges()):
                        g.add_edge(node, nodes[z])
                        new_edge_added = True
   
    return g