import sys

sys.dont_write_bytecode = True

import xml.dom.minidom as minidom

_template_file_g = ""
def set_template_path(path):
    global _template_file_g
    _template_file_g = path

class SVCOMPGraph(object):
    def __init__(self):
        global _template_file_g
        self.__doc = minidom.parse(_template_file_g)

        graph_list = self.__doc.getElementsByTagName('graph')
        assert len(graph_list) == 1
        self.__graph = graph_list[0]

        self.__id_gen=0

    def add_edge(self, source, target, **data_nodes):
        new_edge = self.__doc.createElement('edge')
        # TODO Check if node exist before adding edge???
        new_edge.setAttribute('source', source)
        new_edge.setAttribute('target', target)
        for key, value in data_nodes.items():
            new_data = self.__create_data_node(key, value)
            new_edge.appendChild(new_data)
        self.__graph.appendChild(new_edge)

    def add_new_node(self, **data_nodes):
        self.__id_gen += 1
        nid = 'N' + str(self.__id_gen)
        new_node = self.__doc.createElement('node')
        new_node.setAttribute('id', nid)

        for data in data_nodes:
            new_data = self.__create_data_node(key, value)
            new_node.appendChild(new_data)

        self.__graph.appendChild(new_node) 
        return nid
    def write_graph(self, out_name):
        with open(out_name, "w") as out_file:
            self.__doc.writexml(out_file, addindent="    ", newl="\n")
        out_file.close()

    def __create_data_node(self, key, value):
        new_data = self.__doc.createElement('data')
        new_data.setAttribute('key', key)
        text = self.__doc.createTextNode(value)
        new_data.appendChild(text)
        return new_data

class Proof(object):
    def __init__(self, prog, result_basic):
        self._prog = prog
        self._result_basic = result_basic

    def print_witness(self):
        raise NotImplementedError

class ErrorProof(Proof):
    def print_witness(self, out_name):
        G = SVCOMPGraph()

        trace = self._result_basic.get_function_start_exit_trace()
        nid = G.add_new_node()
        G.add_edge('ENTRY', nid)
        for node in trace:
            old_name = self._prog.find_original_func(node[1])
            if node[0] == 'start':
                new_nid = G.add_new_node()
                G.add_edge(nid, new_nid, enterFunction=old_name)
                nid = new_nid
                new_nid = G.add_new_node()
                assume = ''
                for assign in node[2]:
                    assume += assign[0] + '=' + assign[1] + ';'
                G.add_edge(nid, new_nid, assumption=assume)
                nid = new_nid
            else: # node[0] == 'exit':
                new_nid = G.add_new_node()
                G.add_edge(nid, new_nid, returnFrom=old_name)
                nid = new_nid

        G.add_edge(nid, 'ERROR')
        G.write_graph(out_name)
