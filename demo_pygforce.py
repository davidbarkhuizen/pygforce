import gobject
import gtk

from graph_manipulator import generate_graph
from force_directed_graph import ForceDirectedGraph, AREA_WIDTH, AREA_HEIGHT
from node_tag import Tag
from graphical_event_manager import GEM

TIMER_TICK_PERIOD = 50

def main():
	'''
	generate graph, set time, and launch gtk via gtk.main()
	'''
	# construct test graph
	g = generate_graph(AREA_WIDTH, AREA_HEIGHT)
	
	# launch graphical event manager
	gem = GEM(graph=g)
	
	# tick event period
	tick_event_period = TIMER_TICK_PERIOD
	
	# attach tick event handler
	gem.timer = gobject.timeout_add(tick_event_period, gem.time_tick_handler)
	
	# launch GTK
	gtk.main()

if __name__ == '__main__':
	main()