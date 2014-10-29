import re

from basic_analyzer import AnalysisResultFactory
from basic_analyzer import Pass, Error, Unknown

from cpa_output_reader import ARGHandler, CFAHandler, AbstractionHandler

from formula_utils import b_false, disjunction, substitute

class CPA_Factory:
  @classmethod
  def build(cls, func_names, output_dir):
    # TODO Read config to get filename
    with open(output_dir+"/Statistics.txt", "r") as stats:
      for line in stats:
        pattern = "Verification result: "
        if line.startswith(pattern):
          begin = len(pattern)
          result = (re.search(r"(?P<result>^[A-Z]+)",line[begin:])).group("result")
    stats.close()
 
    if result == 'TRUE'   : return CPA_Pass(func_names, output_dir)
    if result == 'FALSE' : return CPA_Error(func_names, output_dir)
    if result == 'UNKNOWN': return Unknown(func_names, output_dir)
 
    assert 0, 'Error reading result from "' + output_dir + '"'
    return Unknown(func_names, output_dir)

# TODO Construct error path instead of variable assignment
class CPA_Error(Error):
  def __init__(self, func_names, output_dir):
    Error.__init__(self, func_names, output_dir)
    self.__var_assign = None

  def __parse_assignment(self):
    # TODO Read config to get filename
    file_name = self._proof_dir + "ErrorPath.0.assignment.txt"
    self.__var_assign = {}
    with open(file_name, "r") as assignment_file:
      for line in assignment_file:
        pattern = "(?P<var>(\w+::)?\w+)@(?P<seq>\d+) : (?P<type>\w+): (?P<value>[+-]?\d+(?:\.\d+)?)"
        match_obj = re.search(pattern, line)
        if match_obj:
          var = match_obj.group('var')
          seq = int(match_obj.group('seq'))
          value = match_obj.group('value')
          if not var in self.__var_assign:
            self.__var_assign[ var ] = []
          self.__var_assign[ var ].append( (seq, value) )
    assignment_file.close()

    for var, values in self.__var_assign.iteritems():
      values.sort()
      self.__var_assign[var] = map(lambda x: x[1], values)

  def get_variable_assignment(self):
    if not self.__var_assign:
      self.__parse_assignment()
    return self.__var_assign

class CPA_Pass(Pass):
  def __init__(self, func_names, output_dir):
    Pass.__init__(self, func_names, output_dir)
    self.__func2inv_pairs = None

  def __parse_invariants(self):
    # Get ARG nodes in (pre, post_list) for function calls
    # TODO Read config to get filename
    arg_handler = ARGHandler(self._proof_dir+"ARG.dot")
    call_pair_list = list(self.__gen_all_call_pairs(arg_handler))
    # Find formulae from ABS# of cared ARG nodes
    care_abs_list = []
    for call_pair in call_pair_list:
      care_abs_list.append( call_pair['pre']['ABS'] )
      post_list = map(lambda n: n['ABS'], call_pair['post_list'])
      care_abs_list.extend(post_list)

    # TODO Read config to get filename
    abs_handler = AbstractionHandler(
      self._proof_dir+"abstractions.txt",
      care_abs_list
    )

    # Use formulae to compute invariant
    # TODO Read config to get filename
    cfa_handler = CFAHandler(self._proof_dir+"cfainfo.json", self._func_list)
    for call_pair in call_pair_list:
      call_id = call_pair['call_id']
      callee = cfa_handler.get_callee( call_id )
      assert callee == call_pair['pre']['func']

      pre = abs_handler.get_formula(call_pair['pre']['ABS'])
      post_list = map(
        lambda x: abs_handler.get_formula(x['ABS']),
        call_pair['post_list']
      )
      post = disjunction([b_false()] + post_list)
      rcv = cfa_handler.get_receiving_variable( call_id )

      if rcv: # There is a receiving variable
        # Replace receiving variable with formal return parameter
        # TODO Use something other than "r"
        post = substitute(post, (rcv, "r"))

      self.__func2inv_pairs[callee].append( (pre, post) )

  def __gen_all_call_pairs(self, arg_handler):
    func_set = set(self._func_list)

    node_gen = arg_handler.traverse_nodes_dfs()
    stack = []
    for node in node_gen:
      # Function call entry
      if node['type'] == 'entry' and node['func'] in func_set:
        node_id = node['id']
        if stack:
          if node_id == stack[-1]['pre']['id']: 
            # All nodes in subtree are visted
            yield stack.pop()
            continue
        assert node['ABS'] # node must have invariant
        # Find CFA node before this call edge as call_id
        pred = arg_handler.get_only_predecessor(node)
        stack.append( {'call_id': pred['nid'], 'pre': node, 'post_list': []} )
      # Function call exit
      elif node['type'] == 'exit' and node['func'] in func_set:
        assert stack
        node = arg_handler.get_only_successor(node)
        node_id = node['id']
        if stack[-1]['post_list']:
          if node_id == stack[-1]['post_list'][-1]['id']:
            continue # Avoid repeated post nodes
        assert node['ABS'] # node must have invariant
        stack[-1]['post_list'].append( node )

  def get_invariant_pairs(self, func_name):
    if not self.__func2inv_pairs:
      self.__func2inv_pairs = {}
      for func_name in self._func_list:
        self.__func2inv_pairs[ func_name ] = []
      self.__parse_invariants()
    return self.__func2inv_pairs[ func_name ]

