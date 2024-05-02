from typing import List

class LaunchTreeNode:
    def __init__(self, name: str):
        self.name = name
        self.children:List[LaunchTreeNode] = []
    
    def add_child(self, child: 'LaunchTreeNode'):
        self.children.append(child)

class RosNodeTreeNode(LaunchTreeNode):
    def __init__(self, name: str, parameters=None):
        self.name = name
        self.children:List[LaunchTreeNode] = []
        self.parameters = parameters

class LaunchTree:
    def __init__(self):
        self.root = None
        self.edges_manager = []
        self.nodes_manager = {}

    def add_root(self, root_name):
        if self.root is None:
            self.root = LaunchTreeNode(root_name)
            self.nodes_manager[root_name] = self.root
        else:
            print("Root already exists")

    def add_child(self, parent_name, child_name):
        if self.root is None:
            self.root = LaunchTreeNode(parent_name)
            self.nodes_manager[parent_name] = self.root
        
        if parent_name not in self.nodes_manager:
            print(f"Parent node {parent_name} not found")
            return
        
        if child_name in self.nodes_manager:
            print(f"Child node {child_name} already exists")
            return
        
        child = LaunchTreeNode(child_name)
        self.nodes_manager[child_name] = child
        self.nodes_manager[parent_name].add_child(child)
        self.edges_manager.append((parent_name, child_name))

    def add_rosnode_child(self, parent_name, child_name, parameters):
        if self.root is None:
            self.root = LaunchTreeNode(parent_name)
            self.nodes_manager[parent_name] = self.root
        
        if parent_name not in self.nodes_manager:
            print(f"Parent node {parent_name} not found")
            return
        
        if child_name in self.nodes_manager:
            print(f"Child node {child_name} already exists")
            return
        
        child = RosNodeTreeNode(child_name, parameters)
        self.nodes_manager[child_name] = child
        self.nodes_manager[parent_name].add_child(child, parameters)
        self.edges_manager.append((parent_name, child_name))
    
    def plot(self):
        import networkx as nx
        import matplotlib.pyplot as plt
        G = nx.DiGraph()

        G.add_edges_from(self.edges_manager)

        # Calculate positions for each node.
        pos = nx.spring_layout(G)

        import matplotlib.pyplot as plt

        # Draw the nodes
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=700, edge_color='k', linewidths=1, font_size=15)

        # Draw edge labels
        edge_labels = nx.get_edge_attributes(G, 'parameters')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

        plt.show()