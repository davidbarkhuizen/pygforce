import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from graph_manipulator import generate_graph
from graphical_event_manager import GEM
from constants import DEMO_GRAPH_SIZE, DEMO_GRAPH_BRANCHING_CONST, TIMER_TICK_PERIOD


def main():
    '''
    generate a graph, wire up the tick handler, and run the GTK main loop
    '''
    g = generate_graph(DEMO_GRAPH_SIZE, DEMO_GRAPH_BRANCHING_CONST)

    gem = GEM(graph=g)

    gem.timer = GLib.timeout_add(TIMER_TICK_PERIOD, gem.time_tick_handler)

    Gtk.main()


if __name__ == '__main__':
    main()
