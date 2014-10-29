import pdb
import basic_analyzer

from approx import unwind
from approx import under_approx

from func_summary import compute_summary
from func_summary import check_summary

def run(program):
  if program.is_recursive():
    print ("Detected recursive functions:")
    print (program.get_recursive_funcs())
    return overview(program)
  else:
    print ("No obvious recursion detected.")
    print ("Abort.")
    return "Unknown"

def overview(program):
  k = 0

  complete = False

  while not complete:
    k = k + 1

    P_k = unwind(program, k)
    print ("Current unwinding depth: " + str(k))

    G_main = under_approx(P_k)
    print ("Analyzing under-approximation")
    result = basic_analyzer.analyze(G_main)

    if result == 'Error' or result == 'Unknown':
      return result
    # else: # result == Pass
    print ("Computing Candidate of Summaries")
    S = compute_summary(P_k, result)

    print ("Checking Summaries")
    complete = check_summary(P_k, S)

  return 'Pass'

