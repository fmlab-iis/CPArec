import copy

import basic_analyzer
from formula_utils import b_true, b_imply, b_and
from formula_utils import forall_except
from formula_utils import to_C_expression

def compute_summary(prog_k, ind_inv):
  S = dict()
  """
  Find summary for each unwound functions
  """
  for func in prog_k.get_unwound_funcs():
    f = func.get_name()
    S[ f ] = b_true()
    """
    In new algorithm, function calls are no longer inlined.
    Function name should be enough to find invariant pairs.
    """
    for I_s, I_e in ind_inv.get_invariant_pairs( f ):
      if False: # TODO formula_utils.find(func.get_return_parameters(), I_s):
         # This case is of no use currently
         formula = I_e
      else:
         formula = b_imply(I_s, I_e)
      call_S = forall_except(func.get_all_parameters_with_scope(), formula)
      S[ f ] = b_and( S[f], call_S )
    # TODO simplify S[ f ]
  return S

def check_summary(prog_k, S):
  """
  Build a single file for checking all summaries
  """
  prog_chk = copy.deepcopy(prog_k)
  for func in prog_k.get_unwound_funcs(): 
    # TODO Fix this dirty way to get new_name
    old_name = func.get_name()
    new_name = old_name + "_0"
    c_summary = to_C_expression(func, S[old_name])
    """
    Instantiate Summary to new recursive functions after unwinding
    """
    # TODO Replace "1" with comprehensive name
    prog_chk.instantiate_summary( new_name, "1", c_summary )
    """
    Add summary assertion at orignal functions that are unwound now
    """
    # TODO Replace "1" with comprehensive name
    prog_chk.assert_summary( old_name, "1", c_summary )
    prog_chk.inline_function_calls( old_name )

  prog_chk.create_file()
  """
  CheckSummary
  """
  for func in prog_k.get_unwound_funcs():
    result = basic_analyzer.analyze(prog_chk, func.get_name())
    if not result == 'Pass':
      return 'Error'
 
  return 'Pass'
