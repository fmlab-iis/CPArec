
import copy

import transform_manager as transformer

def unwind(prog, k):
  uw_prog = copy.deepcopy(prog)
  uw_prog.unwind(k)
  return uw_prog

def under_approx(prog):
  under_prog = copy.deepcopy(prog)
  for func in prog.get_recursive_funcs():
    # TODO Use comprehensive name instead of "1" "0"
    # Ex: "1": true, "0": false
    under_prog.instantiate_summary( func.get_name(), "1", "0" )
  return under_prog

