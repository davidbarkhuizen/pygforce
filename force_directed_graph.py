import math
from points import Point2D

from constants import *

# X11 colour names -> (r, g, b) in the 0..1 range cairo wants
_RGB = {
    'darkgreen': (0.0, 100 / 255.0, 0.0),
    'black':     (0.0, 0.0, 0.0),
    'blue':      (0.0, 0.0, 1.0),
}

class ForceDirectedGraph(object):

    def __init__(self, graph=None, graphical_event_manager=None):
        self.graph = graph
        self.gem = graphical_event_manager

    def translate(self, x0, y0, w0, h0, w1, h1):
        
        x1 = (float(w1) / 2.0) + float(x0) * (float(w1) / float(w0))
        y1 = (float(h1) / 2.0) - float(y0) * (float(h1) / float(h0)) 
        
        return (x1, y1)

    def reverse(self, x1, y1, w0, h0, w1, h1):
        
        x0 = (float(x1) - ((float(w1) / 2.0))) * (float(w0) / float(w1))
        y0 = ((float(h1) / 2.0) - float(y1)) * (float(h0) / float(h1)) 
        
        return (x0, y0)

    def render(self, cr, node_label_vert_spacing):
        '''
        draw the current graph state onto the cairo context `cr`
        '''

        edge_colour = 'darkgreen'
        node_colour = 'darkgreen'
        text_colour = 'black'

        selected_node_colour = 'blue'
        edges_adj_to_selected_node_colour = 'blue'

        selected_node = None
        selected_nodes = [x for x in self.graph.nodes() if x.is_selected]
        if len(selected_nodes) > 0:
            selected_node = selected_nodes[0]

        # EDGES
        #
        cr.set_line_width(1.0)
        for (i, j) in self.graph.edges():

            if selected_node in (i, j):
                cr.set_source_rgb(*_RGB[edges_adj_to_selected_node_colour])
            else:
                cr.set_source_rgb(*_RGB[edge_colour])

            cr.move_to(i.translated_position.x, i.translated_position.y)
            cr.line_to(j.translated_position.x, j.translated_position.y)
            cr.stroke()

        # NODES
        #
        box_side = 4
        cr.select_font_face("Sans")
        cr.set_font_size(10)
        for node in self.graph.nodes():

            x = node.translated_position.x
            y = node.translated_position.y

            is_selected = node.is_selected

            cr.set_source_rgb(*_RGB[selected_node_colour if is_selected else node_colour])
            cr.rectangle(x - box_side, y - box_side, 2 * box_side, 2 * box_side)
            cr.fill()

            # LABEL / TEXT
            #
            if self.gem.display_node_labels:
                cr.set_source_rgb(*_RGB[selected_node_colour if is_selected else text_colour])
                cr.move_to(x, y - node_label_vert_spacing)
                cr.show_text(node.label)

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

            # k*(r - l): >0 when stretched (pull tag toward other_tag),
            #            <0 when compressed (push tag away from other_tag)
            scalar_force = k * (r - l)

            # unit vector pointing from `tag` toward `other_tag`
            cos_theta = (x_other - x_tag) / r
            sin_theta = (y_other - y_tag) / r

            Fx = scalar_force * cos_theta
            Fy = scalar_force * sin_theta
            
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
        Per-step displacement is the node's current velocity - which
        velocity_at_tag() has already damped with FRICTION and scaled by
        TIME_STEP. step() computes velocity before calling this.
        '''
        return tag.velocity

    def velocity_at_tag(self, tag):
        '''
        V_new = (V_old * FRICTION) + (current net force * TIME_STEP)
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

    def step(self):
        '''
        advance the simulation by one step:
        for each node - net electrostatic force, net spring force, velocity,
        displacement - then apply the displacement and translate to canvas
        coordinates. Rendering is separate (see render()).
        '''

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

            if tag.is_selected and self.gem.b1_down:
                # node is being dragged: hold it, and bleed off momentum so it
                # doesn't get flung when the mouse is released
                tag.velocity = (0.0, 0.0)
            else:
                (dx, dy) = tag.displacement
                tag.position.x = tag.position.x + dx
                tag.position.y = tag.position.y + dy

        # TRANSLATE TO CANVAS
        #
        for node in self.graph.nodes():
            (node.translated_position.x, node.translated_position.y) = self.translate(node.position.x, node.position.y, W_0, H_0, W_1, H_1)
