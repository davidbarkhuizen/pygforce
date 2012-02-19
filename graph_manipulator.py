import networkx as nx
from random import random, randint
from node_tag import Tag
from constants import *

def construct_xy_factory():
    
    used = []
    
    def gen_xy():
        unique = False        
        while not unique:
            x = (- float(W_0) / 2.0) + (random() * float(W_0))
            y = (- float(H_0) / 2.0) + (random() * float(H_0))
            unique = (x,y) not in used
        used.append((x,y))
        return (x,y)

    return gen_xy

def calc_xy_for_new_node(graph):
    
    x = 0
    y = 0
    
    unique = False
    while not unique:
        x = (- float(W_0) / 2.0) +  (random() * float(W_0))
        y = (- float(H_0) / 2.0) + (random() * float(H_0))
        unique = ((x,y) not in [(n.position.x, n.position.y) for n in graph.nodes()])
    
    return (x,y)

def add_edges_for_vertex_at_random(graph, node, max_edges_to_create_per_node_per_pass=2):
    
    nodes = graph.nodes()
    
    for j in range(randint(1, max_edges_to_create_per_node_per_pass)):
    
        new_edge_added = False
        while new_edge_added == False:
            
            edges = graph.edges()
            
            z = randint(0, len(nodes) - 1)
            if nodes[z] != node:
                if ((nodes[z], node) not in edges) and ((node, nodes[z]) not in edges):
                    graph.add_edge(node, nodes[z])
                    new_edge_added = True

def generate_graph(p, max_edges_to_create_per_node_per_pass):
    '''
    generate a semi-random graph of size p
    
    generate p vertices, with random x,y co-ords
    for each vertex:
      randomly add at most max_edges_to_create_per_node_per_pass new edges
    '''
    
    g = nx.Graph()    
    
    f_gen_xy = construct_xy_factory()
    
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

def add_node_to_graph_at_random(graph):
    
    (x, y) = calc_xy_for_new_node(graph)
    tag = Tag(x, y, '')
    tag.label = 'Node %i' % tag.idx    
    graph.add_node(tag)
    
    add_edges_for_vertex_at_random(graph, tag, max_edges_to_create_per_node_per_pass=4)
    
    return tag

def remove_node_from_graph_at_random(graph):
    
    nodes = graph.nodes()            
    idx = randint(0, len(nodes) - 1)            
    node_to_remove = nodes[idx]
    
    graph.remove_node(node_to_remove)
    
    return graph    