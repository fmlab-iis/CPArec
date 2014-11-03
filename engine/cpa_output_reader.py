import re
import networkx
import json

from formula_utils import get_def_list

def grouped(iterable, n):
  return zip(*[iter(iterable)]*n)

class ErrorPathHandler:
  def __init__(self, file_name):
    self.__error_path = []
    self.__parse_error_path(file_name)

  def __parse_error_path(self, file_name):
    # TODO Rewrite as generator
    with open(file_name, 'r') as err_path_file:
      # Read first line and build first edge
      line = err_path_file.next()
      edge = ErrorPathHandler.__parse_line_as_edge(line)
      node = {'nid': edge["source"], 'assign': []} 
      self.__error_path.append(node) # Initial node
      self.__error_path.append(edge)
      node = {'nid': edge["target"], 'assign': []} 
      self.__error_path.append(node)

      for line in err_path_file:
        prev_node = self.__error_path[-1]
        if line.startswith("Line"):
          edge = ErrorPathHandler.__parse_line_as_edge(line)
          node = {'nid': edge['source'], 'assign': []}
          assert node['nid'] == prev_node['nid']
          self.__error_path.append(edge)
          node = {'nid': edge['target'], 'assign': []} 
          self.__error_path.append(node)
        else:
          assign = ErrorPathHandler.__parse_assignment(line)
          # Append assignment to node
          prev_node['assign'].append(assign)

    err_path_file.close()

  def get_error_path(self):
    return self.__error_path

  @classmethod
  def __parse_line_as_edge(cls, line):
    pattern = r"Line (?P<line_no>\d+):\s+N(?P<source>\d+) -{(?P<stmt>[^{}]*)}-> N(?P<target>\d+)"
    match_obj = re.match(pattern, line)
    assert match_obj, 'Malformed edge "'+ line + '" in ErrorPath'
    return match_obj.groupdict()

  @classmethod
  def __parse_assignment(cls, line):
    pattern = "\s+(?P<var>(\w+::)?\w+)@(?P<seq>\d+) : (?P<type>\w+): (?P<value>[+-]?\d+(?:\.\d+)?)"
    match_obj = re.match(pattern, line)
    assert match_obj, "Malformed assignment in ErrorPath"
    assign = match_obj.groupdict()
    assign['seq'] = int( assign['seq'] )
    return assign

class ARGHandler:
  def __init__(self, arg_file_name):
    self.__arg = networkx.read_dot(arg_file_name)

    self.__delete_covering_edges()

  def __delete_covering_edges(self):
    G = self.__arg
    for u, v, data in G.edges_iter(data=True):
      if u'label' in data:
        if data['label'] == u'covered by':
          G.remove_edge(u, v)

  """
  Traverse nodes of ARG by DFS
  Each node is visited twice
  Assuming that ARG without "covered by" edges is a tree
  """
  def traverse_nodes_dfs(self, start = "1"):
    G = self.__arg
    label = G.node[start]["label"]
    yield ARGHandler.__parse_node_label(label)

    stack = [(start, iter(G[start]))]
    while stack:
      parent, children = stack[-1]
      try:
        child = next(children)
        stack.append((child, iter(G[child])))
        label = G.node[child]["label"]
        yield ARGHandler.__parse_node_label(label)
      except StopIteration: # Exception raised by next()
        stack.pop()
        label = G.node[parent]["label"]
        yield ARGHandler.__parse_node_label(label)

  def get_only_successor(self, node):
    G = self.__arg
    ns = G.successors( node["id"] )
    assert len(ns) == 1
    n = ns[0]
    return ARGHandler.__parse_node_label( G.node[n]["label"] )
  def get_only_predecessor(self, node):
    G = self.__arg
    ns = G.predecessors( node["id"] )
    assert len(ns) == 1
    n = ns[0]
    return ARGHandler.__parse_node_label( G.node[n]["label"] )
    

  @classmethod
  def __parse_node_label(cls, node_label):
    nid = r"(?P<id>\d+) @ N(?P<nid>\d+)"
    func = r"\\n(?P<func>\w+)( (?P<type>(entry|exit)))?"
    # XXX Maybe true/false can be used to speed-up
    ABS = r"("+ r"\\nABS(?P<ABS>\d+)(: (true|false))?" + ")?"
    pattern = nid + func + ABS + r"$"
    m = re.match(pattern, node_label)
    assert m, "Cannot parse ARG node label: " + node_label
    node = m.groupdict()
    return node

class CFAHandler():
  def __init__(self, file_name, care_func_list):
    with open(file_name, 'r') as cfa_file:
      cfa_info = json.load(cfa_file)
    cfa_file.close()
 
    care_func_set = set(care_func_list)

    self.__call_dict = dict()
    for edge in cfa_info['edges'].values():
      if edge['type'] == 'CallToReturnEdge':
        call = CFAHandler.__parse_func_call_stmt(edge['stmt'])
        if call['callee'] in care_func_set:
          # Use node before call edge as id of each call
          call_id = str(edge['source'])
          call['caller'] = cfa_info['nodes'][call_id]['func']
          self.__call_dict[ call_id ] = call

  def get_callee(self, call_id):
    return self.__call_dict[call_id]['callee']

  def get_receiving_variable(self, call_id):
    call = self.__call_dict[call_id]
    caller = call['caller']
    rcv_name = call['rcv']
    if rcv_name:
      return caller + "::" + rcv_name
    return None

  @classmethod
  def __parse_func_call_stmt(cls, stmt):
    """
    Assuming every parameter is a single variable
    """
    rcv = r"((?P<rcv>\w+) = )?"
    callee = r"(?P<callee>\w+)"
    args = r"\(" + r"(?P<args>\w+(, \w+)*)?" + r"\);$"
    pattern = rcv + callee + args
    m = re.match(pattern, stmt)
    assert m and m.group('callee'), 'Error parsing CFA edge stmt "' + stmt + '"'
    return m.groupdict()

class AbstractionHandler():
  def __init__(self, file_name, care_abs_list):
    self.__formulae_dict = {x: None for x in care_abs_list}

    smt2_file_name = self.__rewrite_to_smt2(file_name)

    # Here __formulae_dict stores .def#
    care_def_list = self.__formulae_dict.values()
    def_list = get_def_list(smt2_file_name, care_def_list)
    for key in self.__formulae_dict:
      def_id = self.__formulae_dict[key]
      # __formulae_dict stores formula instead of .def#
      self.__formulae_dict[key] = def_list[ def_id ]

  """
  Rewrite file to SMTLib2 format
  Also keep track of mapping from ABS# to assert
  """
  def __rewrite_to_smt2(self, file_name):
    smt2_file_name = file_name + ".smt2"
    with open(file_name, 'r') as abs_file:
      with open(smt2_file_name, 'w') as smt2_file:
        for line in abs_file:
          if not (line.startswith('(') and line.endswith(')\n')):
            break
          smt2_file.write( line )
        assert line == '\n', 'Error splitting "' + file_name + '"'

        # Read three lines a time
        for abs_line, def_line, _ in grouped(abs_file, 3):
          abs_id = AbstractionHandler.__get_abs_id_in_line(abs_line)
          if abs_id in self.__formulae_dict:
            smt2_file.write( def_line ) 
            def_id = AbstractionHandler.__get_def_id_in_line(def_line)
            self.__formulae_dict[abs_id] = def_id
      smt2_file.close()
    abs_file.close()
    return smt2_file_name

  def get_formula(self, abs_id):
    return self.__formulae_dict[abs_id]

  @classmethod
  def __get_abs_id_in_line(cls, id_line):
    abs_id = r"(?P<id>\d+) "
    nbrs_abs_id = r"\(" + r"(\d+(,\d+)*)?" + r"\) "
    nid = r"@(\d+):"
    pattern = abs_id + nbrs_abs_id + nid
    m = re.match(pattern, id_line)
    assert m and m.group('id'), 'Error parsing ABS# from "' + id_line + '"'
    return m.group('id')

  @classmethod
  def __get_def_id_in_line(cls, id_line):
    pattern = r"\(" + r"assert (?P<id>(\.def_\d+)|true|false)"+ r"\)"
    m = re.match(pattern, id_line)
    assert m and m.group('id'), 'Error parsing .def# from "' + id_line + '"'
    return m.group('id')

