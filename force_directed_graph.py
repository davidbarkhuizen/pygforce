import math
from points import *

class Tag(object):

    last_used_idx = 0
    @classmethod
    def pop_unused_idx(cls):
        new_idx = cls.last_used_idx + 1
        cls.last_used_idx = new_idx
        return new_idx        
    
    def __init__(self, x, y, label):
    
        self.idx = Tag.pop_unused_idx()
        
        self.x = x
        self.y = y
        
        self.label = label
        
        self.net_electrostatic_force = (0, 0)
        self.net_spring_force = (0, 0)
        self.displacement = (0, 0)
        self.velocity = (0, 0)

    def __str__(self):
        
        s = ('%i = %s' % (self.idx, self.label)) + '\n'
        s = s + ('(x,y) = (%f,%f)' % (self.x, self.y)) + '\n'
        
        (Fx, Fy) = self.net_electrostatic_force
        s = s + ('electro-static Fx, Fy = %f, %f' % (Fx, Fy)) + '\n'
        
        (Fx, Fy) = self.net_spring_force
        s = s + ('spring Fx, Fy = %f, %f' % (Fx, Fy)) + '\n'    

        (dx, dy) = self.displacement
        s = s + ('displacement dx, dy = %f, %f' % (dx, dy)) + '\n'        
        
        return s

class ForceDirectedGraph(object):
    
    time_step = 0.625
    damping = 0.95
    
    rad_const = math.pi / 180.0  
    
    def rad(self, theta):
        return theta * ForceDirectedGraph.rad_const    
        
    def __init__(self, X_OFFSET, Y_OFFSET, graph=None, ):
        
        self.graph = graph

        self.X_OFFSET = X_OFFSET / 2.0
        self.Y_OFFSET = Y_OFFSET / 2.0

        self.points = []   
        self.edges = []
        
        self.nodes = self.graph.nodes() 
        
        self.x_off = X_OFFSET / 2.0
        self.y_off = Y_OFFSET / 2.0
        self.z_off = 50.0

        self.z_deg = 0
        self.x_deg = 0
        self.y_deg = 0

    def translate(self, x, y):
        
        tX = x + self.X_OFFSET
        tY = y + self.Y_OFFSET
        
        return (tX, tY)

    def generate_points_and_edges(self):
        
        self.points = []
        
        for node in sorted(self.nodes, key=(lambda x : x.idx)):
            
            (tX, tY) = self.translate(node.x, node.y)
            self.points.append(Point2D(x=int(tX), y = int(tY)))        

        self.edges = []

        for (node_A, node_B) in self.graph.edges():
            point_A_idx = [i for i in range(len(self.nodes)) if self.nodes[i] == node_A][0]
            point_B_idx = [i for i in range(len(self.nodes)) if self.nodes[i] == node_B][0]
            self.edges.append((point_A_idx, point_B_idx)) 

    def draw_to_pixmap(self, points, edges, pixmap, gc, style):
        '''
        '''
        # pixmap.draw_line(self.gc, x, y, self.w/2, self.h/2)  

        n = 2
        for point in points:
            pixmap.draw_rectangle(gc, True, point.x - n, point.y - n, n*2, n*2)

        for (i, j) in edges:
            pixmap.draw_line(gc, points[i].x, points[i].y, points[j].x, points[j].y)

    def net_electrostatic_force_at_node(self, tag_A):
        
        Fx_net = 0
        Fy_net = 0
        
        for tag_B in self.graph.nodes():
            
            if tag_B == tag_A:
                continue
           
            delta_x = tag_A.x - tag_B.x
            delta_y = tag_A.y - tag_B.y
            
            r2 = (delta_x * delta_x) + (delta_y * delta_y)
            r = math.sqrt(r2)

            sin_theta = delta_y / r
            cos_theta = delta_x / r

            q_A = 10.0
            q_B = 10.0
            k = 100.0

            scalar_force = k * q_A * q_B / r2
            
            Fy = scalar_force * sin_theta
            Fx = scalar_force * cos_theta
            
            Fy_net = Fy_net + Fy
            Fx_net = Fx_net + Fx
            
        return (Fx_net, Fy_net)

    def net_spring_force_at_node(self, tag):
        
        Fx_net = 0
        Fy_net = 0
        
        for (edge_tag_1, edge_tag_2) in self.graph.edges():
            
            other_tags = [edge_tag_1, edge_tag_2]
            
            if tag not in other_tags:
                continue
           
            other_tag = [t for t in other_tags if t != tag][0]
            
            r2 = math.pow((tag.x - other_tag.x), 2) + math.pow(tag.y - other_tag.y, 2)
            r = math.sqrt(r2)
            
            # CONSTANTS
            #
            k = 0.1
            equilibrium_displacement = 40
            
            scalar_force = - k * (equilibrium_displacement - r)
            
            # DISTINGUISH BETWEEN PUSH & PULL VECTORS
            #            
            if scalar_force < 0:
                (tag_A, tag_B) = (tag, other_tag)                
            else:
                (tag_A, tag_B) = (other_tag, tag)
            
            delta_x = tag_A.x - tag_B.x
            delta_y = tag_A.y - tag_B.y
            
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
        
        xn = xo + ForceDirectedGraph.time_step * xf * ForceDirectedGraph.damping
        yn = yo + ForceDirectedGraph.time_step * yf * ForceDirectedGraph.damping 

        return (xn, yn)

    def iterate(self, pixmap, gc, style):
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
        for tag in self.graph.nodes():
            (dx, dy) = tag.displacement
            tag.x = tag.x + dx
            tag.y = tag.y + dy            
        
        self.generate_points_and_edges()
        self.draw_to_pixmap(self.points, self.edges, pixmap, gc, style)
