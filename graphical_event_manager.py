from random import randint
import gtk
import time
import math

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
        
        self.b1_x = None
        self.b1_y = None
        
        self.mx = None
        self.my = None
        
        self.started = False
        
        self.i = 0
        
        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win.set_title(WIN_TITLE)
        self.gw = W_1
        self.gh = H_1 #int(float(self.gw) / 1.618)
        self.win.resize(self.gw, self.gh)
        self.win.set_position(gtk.WIN_POS_CENTER)
        self.win.connect('destroy', gtk.main_quit)
        #self.win.realize()

        self.da = gtk.DrawingArea()

        self.win.add(self.da)
        self.da.set_size_request(self.gw, self.gh)
        self.win.set_resizable(False)
        
        # REGISTER HANDLERS FOR GTK EVENTS
        
        # WINDOW / PAINT EVENTS
        # 
        self.da.connect("expose-event", self.area_expose_cb)
        
        # MOUSE EVENTS
        #
        self.da.connect("button_press_event", self.button_press_event)
        self.da.connect("button_release_event", self.button_released_event)  
        self.da.connect("motion_notify_event", self.motion_notify_event)
        #self.da.connect("scroll_event", self.scroll_event)
        
        # KEYBOARD EVENTS
        #
        self.win.connect("key-press-event", self.on_key_press_event)
        
        self.da.set_events(
            gtk.gdk.EXPOSURE_MASK 
            | gtk.gdk.BUTTON_PRESS_MASK 
            | gtk.gdk.BUTTON_RELEASE_MASK 
            | gtk.gdk.POINTER_MOTION_MASK
            | gtk.gdk.KEY_PRESS_MASK
         #   gtk.gdk.SCROLL_MASK            
            )
              
        self.da.show()
        self.win.show_all()
    
    def area_expose_cb(self, area, event):
        '''
        '''
        self.area = area
        
        self.style = self.da.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        
        self.w, self.h = area.window.get_size()
        
        self.started = True

        return True                
        
    def button_press_event(self, widget, event):                    

        if (event.button == 1):                        
            
            # NOTE POSITION OF ORIGINAL CLICK
            self.b1_x = event.x
            self.b1_y = event.y
            
            self.b1_down = True
            
            # should do node selection here
            
            self.last_b1_drag_position = (event.x, event.y)
            
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

    def handle_node_select_attempt(self, x1, y1):
        
        x0, y0 = self.force_directed_graph.reverse(x1, y1, W_0, H_0, W_1, H_1)
        
        # distances
        r2s = {} # r2 : Node        
        for node in self.graph.nodes():      
            # r2 = (x - mx0)^2 + (y - my0)^2      
            r2s[node] = math.pow(node.position.x - x0, 2) + math.pow(node.position.y - y0, 2)
           
        for node in r2s.keys():
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
        only run if (self.started == True)
        
        construct gdk pixmap
        draw a white background
        call rot.iterate on pixmap
        draw pixmap to window area
        show change
        '''        
        if (self.started != True):
            return True        
        
        now = time.clock()
        
        # ------------------------------------------------------------------------
        
        # CALC POINTER POSITION
        #
        
#        (mx0, my0) = (0,0)
#        if self.mx and self.my:
#            mx0, my0 = self.force_directed_graph.reverse(self.mx, self.my, W_0, H_0, W_1, H_1)
#            print('Pointer (x0,y0) = (%i, %i), (x1,y1) = (%i, %i)' % (mx0, my0, self.mx, self.my))
        
        # ------------------------------------------------------------------------        
        
        # PERIOIDIC INTERFERENCE WITH SIMULATION - ADD/REMOVE NODE @ RANDOM
        #
        # HANDLE GENERATION ZERO
        #
        if not self.last_generation_timestamp:
            self.last_generation_timestamp = time.clock()     
               
        # HANDLE SUBSEQUENT GENERATIONS
        #
        elif now - self.last_generation_timestamp > GENERATION_INTERVAL:
            
            node_count = len(self.graph.nodes())
            
            min_node_count = DEMO_GRAPH_SIZE / 2
            max_node_count = DEMO_GRAPH_SIZE * 2
            
            # LOWER BOUND ON NODE COUNT
            if node_count <= min_node_count:
                new_node = add_node_to_graph_at_random(self.graph)
            # UPPER BOUND ON NODE COUNT
            elif node_count >= max_node_count:
                remove_node_from_graph_at_random(self.graph)
            # LAISSEZ FAIRE ZONE
            else:
                x = randint(1,2)
                if x % 2 == 0:            
                    remove_node_from_graph_at_random(self.graph)
                else:
                    new_node = add_node_to_graph_at_random(self.graph)
                self.last_generation_timestamp = now
        
        # --------------------------------------------------
        
        # print('\n'*80)
        
        # REPORT POINTER POSITION        
        #
        #print('(W0, H0) = %i, %i | (W1, H1) = %i, %i' % (W_0, H_0, W_1, H_1))
        
        # REPORT ON NODES
        #        
        #print(' ' + ('Idx').rjust(5) + ('x0').rjust(10) + ' ' + ('y0').rjust(10) + ('x1').rjust(10) + ' ' + ('y1').rjust(10))
        for tag in sorted(self.graph.nodes(), key = lambda x : x.idx):
            
            x = tag.position.x
            y = tag.position.y
            idx = tag.idx
            
            tx, ty = self.force_directed_graph.translate(x, y, W_0, H_0, W_1, H_1)
            
            selected_token = '*' if tag.is_selected else ' '
            
            #print(selected_token + ' ' + ('%i' % idx).rjust(5) + ' ' + ('%.2f' % x).rjust(10) + ' ' + ('%.2f' % y).rjust(10)+ ' ' + ('%.2f' % tx).rjust(10) + ' ' + ('%.2f' % ty).rjust(10))
        
        # construct pixmap
        #
        pixmap = gtk.gdk.Pixmap(self.da.window, self.gw, self.gh, depth=-1)
        
        # draw white background
        #
        pixmap.draw_rectangle(self.style.white_gc, True, 0, 0, self.gw, self.gh)
        
        # call rot.iterate on pixmap        
        #
        self.force_directed_graph.iterate(pixmap, self.gc, self.style, NODE_LABEL_VERT_SPACING)        
        
        # draw pixmap to window
        #
        self.area.window.draw_drawable(self.gc, pixmap, 0, 0, 0, 0, -1, -1)  
                
        # show changes
        #
        self.area.show()
      
        return True # return True => repeat
