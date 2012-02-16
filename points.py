class Point2D(object):
    def __init__(self, x=None,y=None):
        self.x = x
        self.y = y
        
class Point3D(object):
    def __init__(self, x=None,y=None,z=None):
        self.x = x
        self.y = y
        self.z = z   

class Node(object):
    
    def __init__(self, neighbours, index, label, x, y):
        '''
        '''
        self.neighbours = neighbours
        self.index = index
        self.label = label
        self.x = x
        self.y = y
        
        



class AdjacencyMatrix(object):
    def __init__(self, vertex_count):
        self.vertex_count = vertex_count
        self.matrix = []
        for j in range(self.vertex_count):
            self.matrix.append([])
        