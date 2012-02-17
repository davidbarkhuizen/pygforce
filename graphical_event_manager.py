import random
import gtk

WIN_TITLE = 'Force-Directed Graphs'
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

from force_directed_graph import *

class GEM(object):
    '''
    graphical event manager
    framework for handling simple process driven and interactive graphics
    '''    
    def __init__(self, graph=None):
        '''
        '''
        
        self.graph = graph
        self.force_directed_graph = ForceDirectedGraph(WINDOW_WIDTH, WINDOW_HEIGHT, graph=self.graph)   
        
        self.b1_down = False
        self.b2_down = False
        self.b3_down = False
        
        self.b1_x = None
        self.b1_y = None
        
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
        
        #for i in dir(area.window): print(i)
        self.started = True

        return True                
        
    def button_press_event(self, widget, event):                    
        '''
        if (event.button == 1):            
            self.b1_x = event.x
            self.b1_y = event.y
            self.b1_down = True
        elif (event.button == 3):            
            self.b3_z = event.x
            self.b3_down = True
        elif (event.button == 2):
            self.b2_down = True  
        elif (event.button == 4):
            print(4)
        elif (event.button == 5):
            print(5)
        '''
        return True

    def motion_notify_event(self, widget, event):
        '''
        record mouse movement, calc deltas
        call self.force_directed_graph.move(d_x, d_y, d_z), passing deltas
        '''
        '''
        if (self.b1_down == True):
            x = event.x
            y = event.y
            
            d_x = x - self.b1_x
            d_y = y - self.b1_y
            d_z = 0
            
            self.b1_x = x
            self.b1_y = y

            self.force_directed_graph.move(d_x, d_y, d_z)
        
        elif (self.b3_down == True):
        
            z = event.x
            
            d_z = z - self.b3_z
            
            d_y = 0
            d_x = 0
            
            self.b3_z = z

            self.force_directed_graph.move(d_x, d_y, d_z)
        '''
        return True
        
    def button_released_event(self, widget, event):   
        '''
        toggle status of b1/b2/b3_down
        '''             
        '''
        if (event.button == 1):
            self.b1_down = False
        elif (event.button == 2):
            self.b2_down = False
        elif (event.button == 3):
            self.b3_down = False     
        '''
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
        
        # construct pixmap
        pixmap = gtk.gdk.Pixmap(self.da.window, self.gw, self.gh, depth=-1)
        # draw white background
        pixmap.draw_rectangle(self.style.white_gc, True, 0, 0, self.gw, self.gh)
        
        # call rot.iterate on pixmap        
        self.force_directed_graph.iterate(pixmap, self.gc, self.style)        
        
        # draw pixmap to window
        self.area.window.draw_drawable(self.gc, pixmap, 0, 0, 0, 0, -1, -1)          
        # show changes
        self.area.show()
      
        return True # return True => repeat
