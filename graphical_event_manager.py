from random import randint
import gtk
import time

WIN_TITLE = 'Force-Directed Graphs'
WINDOW_WIDTH = 900
WINDOW_HEIGHT = int(float(WINDOW_WIDTH) / 1.6)
NODE_LABEL_VERT_SPACING = 5

from force_directed_graph import ForceDirectedGraph, AREA_HEIGHT, AREA_WIDTH
from graph_manipulator import remove_node_from_graph_at_random, add_node_to_graph_at_random, generate_graph

class GEM(object):
    '''
    graphical event manager
    framework for handling simple process driven and interactive graphics
    '''    
    
    # time between random removal of node
    #
    GENERATION_INTERVAL = 5.0 # seconds
    
    def __init__(self, graph=None):
        '''
        '''
        
        self.graph = graph
        self.force_directed_graph = ForceDirectedGraph(WINDOW_WIDTH, WINDOW_HEIGHT, graph=self.graph)   
        self.last_generation_timestamp = None        
        
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
        self.gw = WINDOW_WIDTH
        self.gh = WINDOW_HEIGHT #int(float(self.gw) / 1.618)
        self.win.resize(self.gw, self.gh)
        self.win.set_position(gtk.WIN_POS_CENTER)
        self.win.connect('destroy', gtk.main_quit)
        #self.win.realize()

        self.da = gtk.DrawingArea()

        self.win.add(self.da)
        self.da.set_size_request(self.gw, self.gh)
        self.win.set_resizable(False)
        
        self.da.connect("expose-event", self.area_expose_cb)
        self.da.connect("button_press_event", self.button_press_event)
        self.da.connect("button_release_event", self.button_released_event)  
        self.da.connect("motion_notify_event", self.motion_notify_event)
        #self.da.connect("scroll_event", self.scroll_event)
            
        self.da.set_events(
            gtk.gdk.EXPOSURE_MASK | 
            gtk.gdk.BUTTON_PRESS_MASK | 
            gtk.gdk.BUTTON_RELEASE_MASK | 
            gtk.gdk.POINTER_MOTION_MASK #| 
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
            self.b1_x = event.x
            self.b1_y = event.y
            self.b1_down = True
            
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

        self.mx = event.x
        self.my = event.y

        if (self.b1_down == True):
            x = event.x
            y = event.y
            
            d_x = x - self.b1_x
            d_y = y - self.b1_y
            
            self.b1_x = x
            self.b1_y = y

            # self.force_directed_graph.move(d_x, d_y, d_z)
        
        elif (self.b3_down == True):
            pass
            # self.force_directed_graph.move(d_x, d_y, d_z)

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
        
        print('\n'*80)
        
        now = time.clock()
        
        if not self.last_generation_timestamp:
            self.last_generation_timestamp = time.clock()
        elif now - self.last_generation_timestamp > GEM.GENERATION_INTERVAL:
            
            node_count = len(self.graph.nodes())
            
            min_node_count = 5
            max_node_count = 20
            
            # LOWER BOUND ON NODE COUNT
            if node_count <= min_node_count:
                new_node = add_node_to_graph_at_random(self.graph, AREA_WIDTH, AREA_HEIGHT)
            # UPPER BOUND ON NODE COUNT
            elif node_count >= max_node_count:
                remove_node_from_graph_at_random(self.graph)
            # LAISSEZ FAIRE ZONE
            else:
                x = randint(1,2)
                if x % 2 == 0:            
                    remove_node_from_graph_at_random(self.graph)
                else:
                    new_node = add_node_to_graph_at_random(self.graph, AREA_WIDTH, AREA_HEIGHT)
                self.last_generation_timestamp = now
        
        if self.mx and self.my:
        
            reversed_x = self.mx - self.force_directed_graph.X_OFFSET
            reversed_y = self.my - self.force_directed_graph.Y_OFFSET
            
            print('pointer - (%i, %i) -> (%i, %i)' % (self.mx, self.my, reversed_x, reversed_y))
        
        print(('Idx').rjust(5) + ('x').rjust(10) + ' ' + ('y').rjust(10))
        for tag in sorted(self.graph.nodes(), key = lambda x : x.idx):
            
            x = tag.position.x
            y = tag.position.y
            idx = tag.idx
            
            print(('%i' % idx).rjust(5) + ' ' + ('%.2f' % x).rjust(10) + ' ' + ('%.2f' % y).rjust(10))
        
        # construct pixmap
        pixmap = gtk.gdk.Pixmap(self.da.window, self.gw, self.gh, depth=-1)
        
        # draw white background
        pixmap.draw_rectangle(self.style.white_gc, True, 0, 0, self.gw, self.gh)
        
        # call rot.iterate on pixmap        
        self.force_directed_graph.iterate(pixmap, self.gc, self.style, NODE_LABEL_VERT_SPACING)        
        
        # draw pixmap to window
        self.area.window.draw_drawable(self.gc, pixmap, 0, 0, 0, 0, -1, -1)  
                
        # show changes
        self.area.show()
      
        return True # return True => repeat
