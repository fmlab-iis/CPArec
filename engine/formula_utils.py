import fileinput
import linecache
import re

import smtlib_parser
import redlog_manager as rl_mgr

def get_def_list(smt2_file_name, care_def_list):
  """
  Return list of formulae in all assertions
  Assertions are of the same order as in the file
  """
  smt2rl = SMTLib2Redlog(smt2_file_name, care_def_list)
  return smt2rl.get_def_rlexpr_map()

def b_true():
  return "true"

def b_false():
  return "false"

def b_imply(a, b):
  return "(" + a + ")impl(" + b + ")"

def b_and(*expr_list):
  return b_n_ary_op("and", *expr_list)

def b_or(*expr_list):
  return b_n_ary_op("or", *expr_list)
 
def b_n_ary_op(op, *expr_list):
  assert len(expr_list) != 0
  string = ''
  for expr in expr_list:
    assert expr != ''
    string = string + ' ( ' + expr + ' ) ' + op
  return string[:-len(op)]

_var_pattern_g = r'{(?P<var>([_A-Za-z]\w*::)?[_A-Za-z]\w*)}'
def _get_vars(formula):
  global _var_pattern_g
  var_list = [m.group('var') for m in re.finditer(_var_pattern_g, formula)]
  return set(var_list)

def _remove_indicator(formula):
  return formula.replace('{','').replace('}','')

def forall_except(var_list, formula):
  remain_vars = set(var_list)
  vars_in_formula = _get_vars(formula)

  bounded_vars = vars_in_formula.difference(remain_vars)
 
  # TODO try save time here
  # Cannot return formula because not simplified 
  '''
  if len(bounded_vars) == 0:
    return formula
  '''
  rlvar_dict = {}
  qe_list = []
  i = 0
  new_formula = formula
  for var in vars_in_formula:
    rlvar = "rlvar_" + str(i)
    i += 1
    rlvar_dict[rlvar] = var
    if var in bounded_vars:
      qe_list.append(rlvar)

  list_sub = [(sec, fst) for fst, sec in rlvar_dict.items()]
  new_formula = substitute(formula, *list_sub)
  # Remove invalid characters
  new_formula = _remove_indicator(new_formula)
  # Call quantifier
  new_formula = rl_mgr.eliminateQuantifier(new_formula, qe_list)

 
  def replace_func(match_obj):
    name = match_obj.group(0)
    assert name in rlvar_dict
    return '{' + rlvar_dict[name] + '}'
  new_formula = re.sub("rlvar_\d+", replace_func, new_formula)
  return new_formula

def disjunction(expr_list):
  return b_or(*expr_list)
def conjunction(expr_list):
  return b_and(*expr_list)

def find(formula, var_list):
  # TODO Not used currently
  raise NotImplementedError

def substitute(formula, *pairs):
  global _var_pattern_g
  new_formula = formula
  # TODO Change to use repl function for efficiency
  for old, new in pairs:
    new_formula = re.sub('{'+old+'}', '{'+new+'}', new_formula)
  return new_formula

def to_C_expression(func, formula):
  # TODO Buggy
  if formula == "true":
    return "1"
  elif formula == "false":
    return "0"
  # else:
  '''
  Replace operators
  '''
  _rl_op_dict_g = {
    "and":"&&", "or":"||", "not":"!",
    "=":"==", "<>":"!=", "true":"1", "false":"0"
  }
  _rl_rex_g = r" (?P<op>("
  for key in _rl_op_dict_g.keys():
    _rl_rex_g += key + "|"
  _rl_rex_g = _rl_rex_g[:-1] + r")) "
  formula = re.sub(_rl_rex_g, lambda x: _rl_op_dict_g[x.group("op")], formula)
  '''
  Remove variable scope
  '''
  pairs = [(func.add_scope(x), x) for x in func.get_input_parameters()]
  formula = substitute(formula, *pairs)
  '''
  Remove variable indicator
  '''
  formula = _remove_indicator(formula)
  return formula

class SMTLib2Redlog:
  def __init__(self, file_name, care_def_list):
    self.__file_name = file_name
    self._def_line_map = {}
    #Initial Definitions
    self.__def_rlexpr_map = {"true":"true", "false":"false"}
    # Check if the file is modified
    linecache.checkcache(self.__file_name)
    self.__read_file()
    for def_id in set(care_def_list):
      rlexpr = self.__build_rlexpr_by_def(def_id)
      # The built expression should have been stored
      assert rlexpr == self.__def_rlexpr_map[def_id]
    self._def_line_map.clear()

  def get_def_rlexpr_map(self):
    return self.__def_rlexpr_map

  def __read_file(self):
    abs_file = fileinput.input(self.__file_name)
    # Read SMTLib2 commands
    for line in abs_file:
      if( not smtlib_parser.isSMTLibCommand(line) ):
        assert line == "\n"
      elif( smtlib_parser.isDefineFunction(line) ):
        def_name = smtlib_parser.getDefineFunctionName(line)
        self._def_line_map[def_name] = abs_file.filelineno()
    abs_file.close()

  def __build_rl_operand(self, operand):
    assert type(operand) == str or type(operand) == list
    if type(operand) == list:
       return self._buildCExprFromList(operand)

    if operand in self._def_line_map :
      ret = self.__build_rlexpr_by_def(operand)
    elif operand.startswith("|"):
      assert operand.endswith("|")
      ret = "{" + (operand.strip("|")) + "}"
    else :
      ret = operand
    return ret

  def _buildCExprFromList(self, prefix_list):
    assert len(prefix_list)==2 or len(prefix_list)==3
    # Parse Operator and First Operand
    cexpr_op = smtlib_parser.toCOperator(prefix_list[0])
    cexpr_l = self.__build_rl_operand(prefix_list[1])
    if( len(prefix_list)==3 ):
      # Parse Second Operand
      cexpr_r = self.__build_rl_operand(prefix_list[2])
      ret = cexpr_l+cexpr_op+cexpr_r
    else:
      ret = cexpr_op + cexpr_l
    return '('+ ret +')'

  def __build_rlexpr_by_def(self, smt_def):
    if(smt_def in self.__def_rlexpr_map):
      return self.__def_rlexpr_map[smt_def]
    assert smt_def in self._def_line_map
    line = linecache.getline(self.__file_name, self._def_line_map[smt_def])
    # FIXME This is an extremely simple way to get formulae. Refine Later
    tmp_list = smtlib_parser.tokenize((line.strip(" \n")))
    prefix_list = tmp_list[4]
    ret = self._buildCExprFromList(prefix_list)
    # Record translated expressions
    self.__def_rlexpr_map[smt_def] = ret
    return ret;
