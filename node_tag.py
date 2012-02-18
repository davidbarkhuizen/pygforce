from points import Point2D

from constants import *

class Tag(object):

    last_used_idx = 0
    @classmethod
    def pop_unused_idx(cls):
        new_idx = cls.last_used_idx + 1
        cls.last_used_idx = new_idx
        return new_idx        
    
    def __init__(self, x, y, label):
    
        self.idx = Tag.pop_unused_idx()        
        
        self.position = Point2D(x, y)
        self.translated_position = Point2D(x, y)
        
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