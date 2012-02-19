import math
import gtk
from points import Point2D

from constants import *

class ForceDirectedGraph(object):
        
    def __init__(self, graph=None, ):
        self.graph = graph

    def translate(self, x0, y0, w0, h0, w1, h1):
        
        x1 = (float(w1) / 2.0) + float(x0) * (float(w1) / float(w0))
        y1 = (float(h1) / 2.0) - float(y0) * (float(h1) / float(h0)) 
        
        return (x1, y1)

    def reverse(self, x1, y1, w0, h0, w1, h1):
        
        x0 = (float(x1) - ((float(w1) / 2.0))) * (float(w0) / float(w1))
        y0 = ((float(h1) / 2.0) - float(y1)) * (float(h0) / float(h1)) 
        
        return (x0, y0)

    def draw_to_pixmap(self, pixmap, gc, style, node_label_vert_spacing):
        '''
        '''
        # pixmap.draw_line(self.gc, x, y, self.w/2, self.h/2)  

        box_side = 2
        for node in self.graph.nodes():
            
            x = int(node.translated_position.x)
            y = int(node.translated_position.y)
            
            #for x in dir(gc): print(x)
            
            orig_fg_color = gc.foreground

            COLOUR_ORANGE = "#FF8000"
            COLOURS = ['red', 'green', 'blue', 'purple', 'red_float', 'green_float', 'blue_float']

            is_selected = node.is_selected 
            if is_selected:
                gc.set_foreground(pixmap.get_colormap().alloc_color("red")) 

            # NODE = BOX
            pixmap.draw_rectangle(gc, True, x - box_side, y - box_side, 2*box_side, 2*box_side)
            
            # LABEL / TEXT
            font = style.get_font()
            pixmap.draw_text(font, gc, x, y - node_label_vert_spacing, node.label)
            
            # revert to normal node color
            if is_selected:
                gc.set_foreground(orig_fg_color)
            
        # EDGES
        #
        for (i, j) in self.graph.edges():
            pixmap.draw_line(gc, int(i.translated_position.x), int(i.translated_position.y), int(j.translated_position.x), int(j.translated_position.y))

    def net_electrostatic_force_at_node(self, tag_A):
        
        Fx_net = 0.0
        Fy_net = 0.0
        
        for tag_B in self.graph.nodes():
            
            if tag_B == tag_A:
                continue
           
            xA = tag_A.position.x
            yA = tag_A.position.y
            
            xB = tag_B.position.x
            yB = tag_B.position.y
           
            delta_x = xA - xB
            delta_y = yA - yB
            
            r2 = (delta_x * delta_x) + (delta_y * delta_y)
            r = math.sqrt(r2)
            
            if r == 0.0:
                continue
            
            sin_theta = delta_y / r
            cos_theta = delta_x / r            

            q_A = 10.0
            q_B = 10.0
            k = 100.0

            scalar_force = k * q_A * q_B / math.pow(r, 1.9)
            
            Fy = scalar_force * sin_theta
            Fx = scalar_force * cos_theta
            
            Fy_net = Fy_net + Fy
            Fx_net = Fx_net + Fx
            
        return (Fx_net, Fy_net)

    def net_spring_force_at_node(self, tag):
        
        Fx_net = 0
        Fy_net = 0
        
        x_tag = tag.position.x
        y_tag = tag.position.y        
        
        for (edge_tag_1, edge_tag_2) in self.graph.edges():
            
            other_tags = [edge_tag_1, edge_tag_2]
            
            if tag not in other_tags:
                continue
           
            other_tag = [t for t in other_tags if t != tag][0]
            
            x_other = other_tag.position.x
            y_other = other_tag.position.y
            
            
            r2 = math.pow((x_tag - x_other), 2) + math.pow(y_tag - y_other, 2)
            r = math.sqrt(r2)
            
            if r == 0.0:
                continue
            
            # PHYSICS CONSTANTS
            #           
            k = SPRING_CONSTANT
            l = EQUILIBRIUM_DISPLACEMENT
           
            scalar_force = - k * (l - r)
            
            # DISTINGUISH BETWEEN PUSH & PULL VECTORS
            #            
            if scalar_force < 0:
                (tag_A, tag_B) = (tag, other_tag)                
            else:
                (tag_A, tag_B) = (other_tag, tag)
            
            delta_x = tag_A.position.x - tag_B.position.x
            delta_y = tag_A.position.y - tag_B.position.y
            
            sin_theta = delta_y / r
            cos_theta = delta_x / r
    
            Fy = scalar_force * sin_theta
            Fx = scalar_force * cos_theta
            
            Fy_net = Fy_net + Fy
            Fx_net = Fx_net + Fx
            
        return (Fx_net, Fy_net)

    def net_force_at_node(self, tag):
        '''
        net Force = net Electrostatic Force + net Spring Force
        '''        
        eX, eY = tag.net_electrostatic_force
        sX, sY = tag.net_spring_force
        
        nX = eX + sX
        nY = eY + sY 
        
        return (nX, nY) 

    def displacement_at_node(self, tag):
        '''
        ERROR - DISPLACEMENT IS NOT USING VELOCITY
        '''        
        eX, eY = tag.net_electrostatic_force
        sX, sY = tag.net_spring_force
        
        nX = eX + sX
        nY = eY + sY 
        
        displacement = (nX, nY)
        
        return displacement    

    def velocity_at_tag(self, tag):
        '''
        ERROR !! VELOCITY IS NOT BEING USED TO DETERMINED DISPLACEMENT, ONLY NET FORCE
        
        V_new = (V_old * Friction) + (current NET FORCE * TIME_STEP)
        '''
        
        (xf, yf) = self.net_force_at_node(tag)
        
        # RECORD PREVIOUS VELOCITY
        #
        (xo, yo) = tag.velocity
        
        friction = FRICTION 
        time_step = TIME_STEP
        
        # NEW V = (OLD V * FRICTION) + (CURRENT NET FORCE * TIME_STEP)
        #
        xn = (xo * friction) + xf * time_step 
        yn = (yo * friction) + yf * time_step

        return (xn, yn)

    def iterate(self, pixmap, gc, style, node_label_vertical_spacing):
        '''
        for each node
            calc net electrostatic force
            calc net spring force
            calc displacement [impulse]
            effect displacements
        '''

        # ------------------------------------
        
        
        # ------------------------------------
        # FOR EACH NODE 

        # CALCULATE NET FORCE
        #
        for tag in self.graph.nodes():
            tag.net_electrostatic_force = self.net_electrostatic_force_at_node(tag)

        for tag in self.graph.nodes():
            tag.net_spring_force = self.net_spring_force_at_node(tag)        
        
        # CALC VELOCITY
        #
        for tag in self.graph.nodes():
            tag.velocity = self.velocity_at_tag(tag)
        
        # CALC DISPLACEMENT
        #
        for tag in self.graph.nodes():
            tag.displacement = self.displacement_at_node(tag)
        
        # ADJUST POSITION
        #
        for tag in self.graph.nodes():
            (dx, dy) = tag.displacement
            tag.position.x = tag.position.x + dx
            tag.position.y = tag.position.y + dy            
        
        # TRANSLATE TO CANVAS
        #
        for node in self.graph.nodes():
            (node.translated_position.x, node.translated_position.y) = self.translate(node.position.x, node.position.y, W_0, H_0, W_1, H_1)
        
        # CALL RENDERING METHOD
        #
        self.draw_to_pixmap(pixmap, gc, style, node_label_vertical_spacing)
