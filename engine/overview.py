import sys
from six import print_

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
    # TODO Directly use basic_analyzer to analyze
    print ("Abort.")
    return "Unknown"

def overview(program):
  k = 0

  complete = False

  while not complete:
    k = k + 1

    print_progress ("Unwinding: " + str(k))
    P_k = unwind(program, k)

    G_main = under_approx(P_k)
    print_progress (" -> Analyzing under-approximation: ")
    result = basic_analyzer.analyze(G_main)
    print (result)

    if result == 'Error' or result == 'Unknown':
      return result
    # else: # result == Pass
    print_progress (" -> Computing Summaries")
    S = compute_summary(P_k, result)

    print_progress (" -> Checking Summaries: ")
    result = check_summary(P_k, S)
    print (result)
    complete = (result == 'Pass')

  return result

def print_progress(string):
  print_ (string, end='')
  sys.stdout.flush()
