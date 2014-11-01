import sys

sys.dont_write_bytecode = True

import xml.dom.minidom as minidom

_template_file_g = ""
def set_template_path(path):
    global _template_file_g
    _template_file_g = path

class Proof(object):
    def __init__(self, prog, result_basic):
        self.__prog = prog
        self.__result_basic = result_basic

    def print_witness(self):
        raise NotImplementedError

class ErrorProof(Proof):
    def print_witness(self, out_name):
        global _template_file_g
        doc = minidom.parse(_template_file_g)

        graph_list = doc.getElementsByTagName('graph')
        assert len(graph_list) == 1

        # TODO produce real witness
        # TODO Wrap XML DOM operation ro graph operation
        graph = graph_list[0]
        new_edge = doc.createElement('edge')
        new_edge.setAttribute('source', 'ENTRY')
        new_edge.setAttribute('target', 'ERROR')

        graph.appendChild(new_edge)

        with open(out_name, "w") as out_file:
            doc.writexml(out_file, addindent="    ", newl="\n")
        out_file.close()

