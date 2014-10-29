import subprocess
import os

_exe_path_g = ""
_script_path_g = ""
_out_path_g = ""

def setExePath(exe_path):
  global _exe_path_g
  _exe_path_g = exe_path

def setScriptPath(script_path):
  global _script_path_g
  _script_path_g = script_path

def setOutputPath(out_path):
  global _out_path_g
  _out_path_g = out_path

def _getDefaultArgs():
  global _exe_path_g
  if _exe_path_g == "" or _script_path_g == "":
    raise Exception
  default_args = [_exe_path_g]
  # Feed script
  default_args.append(_script_path_g)
  return default_args
  
def eliminateQuantifier(formula, var_list):
  # Write scripts for executing redlog
  cmd = "off nosplit;\n"
  cmd += "load_package redlog;\n"
  cmd += "rlset pasf;\n"
  if not var_list:
    cmd += "psi := (" + formula + ");\n"
  else:
    rl_list = '{'
    for var in var_list:
      rl_list += var + ','
    rl_list = rl_list[:-len(',')] + '}'
    cmd += "psi := all(" + rl_list + ',' + formula + ");\n"
  cmd += "out \"" + _out_path_g + "\";\n"
  cmd += "rlqe psi;\n"
  cmd += "shut \"" + _out_path_g + "\";\n"
  cmd += "quit;"
  with open(_script_path_g, "w") as script_file:
    script_file.write(cmd)
  script_file.close()

  args = _getDefaultArgs()
  with open(os.devnull, "w") as null_file:
   subprocess.call(args, stdout=null_file)
  null_file.close()
  with open(_out_path_g, "r") as summary_file:
    expr = summary_file.read().replace('\n', '')
  summary_file.close()
  return expr
