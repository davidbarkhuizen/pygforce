import math

import gtk

from points import Point2D

class ForceDirectedGraph(object):
        
    TIME_STEP = 0.8
    FRICTION = 0.95
    
    SPRING_CONSTANT = 0.1
    EQUILIBRIUM_DISPLACEMENT = 30
        
    def __init__(self, CANVAS_WIDTH, CANVAS_HEIGHT, graph=None, ):
        
        self.graph = graph

        self.X_OFFSET = CANVAS_WIDTH / 2.0
        self.Y_OFFSET = CANVAS_HEIGHT / 2.0

    def translate(self, x, y):
        
        tX = x + self.X_OFFSET
        tY = y + self.Y_OFFSET
        
        return (tX, tY)

    def draw_to_pixmap(self, pixmap, gc, style, node_label_vert_spacing):
        '''
        '''
        # pixmap.draw_line(self.gc, x, y, self.w/2, self.h/2)  

        box_side = 2
        for node in self.graph.nodes():
            
            x = int(node.translated_position.x)
            y = int(node.translated_position.y)
            
            # NODE = BOX
            pixmap.draw_rectangle(gc, True, x - box_side, y - box_side, 2*box_side, 2*box_side)
            
            # LABEL / TEXT
            font = style.get_font()
            pixmap.draw_text(font, gc, x, y - node_label_vert_spacing, node.label)
            
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
            
            # CONSTANTS
            #
           
            k = ForceDirectedGraph.SPRING_CONSTANT
            l = ForceDirectedGraph.EQUILIBRIUM_DISPLACEMENT
           
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
        '''        
        eX, eY = tag.net_electrostatic_force
        sX, sY = tag.net_spring_force
        
        nX = eX + sX
        nY = eY + sY 
        
        return (nX, nY) 

    def displacement_at_node(self, tag):
        '''
        '''        
        eX, eY = tag.net_electrostatic_force
        sX, sY = tag.net_spring_force
        
        nX = eX + sX
        nY = eY + sY 
        
        displacement = (nX, nY)
        
        return displacement    

    def velocity_at_tag(self, tag):
        
        (xf, yf) = self.net_force_at_node(tag)
        
        (xo, yo) = tag.velocity
        
        friction = ForceDirectedGraph.FRICTION 
        time_step = ForceDirectedGraph.TIME_STEP
        
        xn = (xo * friction) + xf * time_step 
        yn = (yo * friction) + yf * time_step

        return (xn, yn)

    def iterate(self, pixmap, gc, style, node_label_vertical_spacing):
        '''
        '''
        # for each node
        #   calc net electrostatic force
        #   calc net spring force
        #   calc displacement [impulse]
        #   effect displacements
        # generate point array

        for tag in self.graph.nodes():
            tag.net_electrostatic_force = self.net_electrostatic_force_at_node(tag)

        for tag in self.graph.nodes():
            tag.net_spring_force = self.net_spring_force_at_node(tag)        
        
        for tag in self.graph.nodes():
            tag.velocity = self.velocity_at_tag(tag)
        
        for tag in self.graph.nodes():
            tag.displacement = self.displacement_at_node(tag)
        
#        print('\n'*80)
#        for tag in self.graph.nodes():
#            print(tag)
#
        # ADJUST POSITION
        for tag in self.graph.nodes():
            (dx, dy) = tag.displacement
            tag.position.x = tag.position.x + dx
            tag.position.y = tag.position.y + dy            
        
        # TRANSLATE TO CANVAS
        #
        for node in self.graph.nodes():
            (node.translated_position.x, node.translated_position.y) = self.translate(node.position.x, node.position.y)
        
        self.draw_to_pixmap(pixmap, gc, style, node_label_vertical_spacing)
