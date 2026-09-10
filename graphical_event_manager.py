from random import randint
import time
import math

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from constants import *

from force_directed_graph import ForceDirectedGraph
from graph_manipulator import remove_node_from_graph_at_random, add_node_to_graph_at_random, generate_graph

class GEM(object):
    '''
    graphical event manager
    framework for handling simple process driven and interactive graphics
    '''    
    
    def __init__(self, graph=None):
        '''
        '''
        
        self.graph = graph
        
        self.force_directed_graph = ForceDirectedGraph(graph=self.graph, graphical_event_manager=self)   
        self.last_generation_timestamp = None        
        
        self.display_node_labels = False
        
        self.b1_down = False
        self.b2_down = False
        self.b3_down = False

        self.gw = W_1
        self.gh = H_1

        self.win = Gtk.Window()
        self.win.set_title(WIN_TITLE)
        self.win.set_position(Gtk.WindowPosition.CENTER)
        self.win.set_resizable(False)
        self.win.connect('destroy', Gtk.main_quit)

        self.da = Gtk.DrawingArea()
        self.da.set_size_request(self.gw, self.gh)
        self.win.add(self.da)

        # REGISTER HANDLERS FOR GTK EVENTS

        # PAINT
        self.da.connect('draw', self.on_draw)

        # MOUSE
        self.da.connect('button-press-event', self.button_press_event)
        self.da.connect('button-release-event', self.button_released_event)
        self.da.connect('motion-notify-event', self.motion_notify_event)

        # KEYBOARD
        self.win.connect('key-press-event', self.on_key_press_event)

        self.da.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        self.win.show_all()

    def on_draw(self, widget, cr):
        # white background
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.paint()

        self.force_directed_graph.render(cr, NODE_LABEL_VERT_SPACING)

        return False

    def button_press_event(self, widget, event):

        if (event.button == 1):

            self.b1_down = True

            self.handle_node_select_attempt(event.x, event.y)
            
            # translated x,y for button press canvaS x,y
            # check which nodes are within selection volume
            # find the closest of the nodes
            # select it
            # change node colour based on selection
            #     potentially change colour of adjacent edges, and neighbout nodes
        
        elif (event.button == 3):            
            self.b3_z = event.x
            self.b3_down = True
        
        elif (event.button == 2):
            self.b2_down = True  
        
        elif (event.button == 4):
            pass
        
        elif (event.button == 5):
            pass

        return True

    def motion_notify_event(self, widget, event):
        '''
        record mouse movement, calc deltas
        call self.force_directed_graph.move(d_x, d_y, d_z), passing deltas
        '''

        if (self.b1_down == True):
            
            (x_1_now, y_1_now) = (event.x, event.y)
            (x_0_now, y_0_now) = self.force_directed_graph.reverse(x_1_now, y_1_now, W_0, H_0, W_1, H_1)
            
            selected_nodes = [x for x in self.graph.nodes() if x.is_selected]
            
            if len(selected_nodes) > 0:            

                selected_node = selected_nodes[0]
    
                selected_node.position.x = x_0_now
                selected_node.position.y = y_0_now 
      
        elif (self.b3_down == True):
            pass

        return True
        
    def button_released_event(self, widget, event):   
        '''
        toggle status of b1/b2/b3_down
        '''             

        if (event.button == 1):
            self.b1_down = False
        elif (event.button == 2):
            self.b2_down = False
        elif (event.button == 3):
            self.b3_down = False     

        return True   

    def on_key_press_event(self, widget, event):
        self.display_node_labels = not self.display_node_labels
        return True

    def handle_node_select_attempt(self, x1, y1):
        
        x0, y0 = self.force_directed_graph.reverse(x1, y1, W_0, H_0, W_1, H_1)
        
        # distances
        r2s = {} # r2 : Node        
        for node in self.graph.nodes():      
            # r2 = (x - mx0)^2 + (y - my0)^2      
            r2s[node] = math.pow(node.position.x - x0, 2) + math.pow(node.position.y - y0, 2)
           
        for node in list(r2s.keys()):
            r2 = r2s[node]
            if r2 > (MINIMUM_NODE_SELECTION_RADIUS * MINIMUM_NODE_SELECTION_RADIUS):
                r2s.pop(node)
        
        closest_node = None
        if len(r2s) > 0:
            sorted_nodes = sorted(r2s.keys(), key = lambda x : r2s[x])
            closest_node = sorted_nodes[0]
        
        for node in self.graph.nodes():
            # RESET ALL OTHER NODES
            if node != closest_node:
                node.is_selected = False
            # TOGGLE SELECTION ON TRAGET NODE
            elif node == closest_node:
                node.is_selected = not node.is_selected 
                
    def time_tick_handler(self):
        '''
        periodic simulation tick, driven by GLib.timeout_add:
        maybe add/remove a node, advance the physics, request a repaint.
        '''

        now = time.time()

        # ------------------------------------------------------------------------

        # PERIODIC INTERFERENCE WITH SIMULATION - ADD/REMOVE NODE @ RANDOM
        #
        # HANDLE GENERATION ZERO
        #
        if not self.last_generation_timestamp:
            self.last_generation_timestamp = now

        # HANDLE SUBSEQUENT GENERATIONS
        #
        elif now - self.last_generation_timestamp > GENERATION_INTERVAL:

            node_count = len(self.graph.nodes())

            min_node_count = DEMO_GRAPH_SIZE // 2
            max_node_count = DEMO_GRAPH_SIZE * 2

            # LOWER BOUND ON NODE COUNT
            if node_count <= min_node_count:
                add_node_to_graph_at_random(self.graph)
            # UPPER BOUND ON NODE COUNT
            elif node_count >= max_node_count:
                remove_node_from_graph_at_random(self.graph)
            # LAISSEZ FAIRE ZONE
            else:
                if randint(1, 2) % 2 == 0:
                    remove_node_from_graph_at_random(self.graph)
                else:
                    add_node_to_graph_at_random(self.graph)

            # reset the interval timer whichever branch ran, otherwise a graph
            # sitting at the min/max bound keeps generating on every tick
            self.last_generation_timestamp = now

        # --------------------------------------------------

        # advance the simulation and ask the drawing area to repaint
        #
        self.force_directed_graph.step()
        self.da.queue_draw()

        return True  # return True => keep the timeout running
