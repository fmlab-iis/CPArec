import os
import tempfile
import shutil

from transform_manager import Program
import overview

import basic_analyzer
import redlog_manager as rl_mgr

from cpa_checker import CPA_Factory
from proof_report import ErrorProof

_this_dir_g = os.path.dirname(__file__)

def _abs_path(rel_path):
  global _this_dir_g
  return os.path.join(_this_dir_g, rel_path)

_tmp_dir_g = tempfile.mkdtemp(prefix="CPArec-",dir = "/tmp/")


# TODO better contorl of configuration
transform_manager.set_tran_path(_abs_path("../tran/tran.native"))
transform_manager.set_output_path(_tmp_dir_g)

rl_mgr.setExePath(_abs_path("../ext_quantifier/reduce/reduce"))
rl_mgr.setScriptPath((_tmp_dir_g + "/rl_script"))
rl_mgr.setOutputPath((_tmp_dir_g + "/rl_summary"))

options = {
  "bin_file"  :_abs_path("../ext_analyzer/CPAchecker-1.2.11-svcomp14b-unix/scripts/cpa.sh"),
  "conf_file" :_abs_path("../ext_analyzer/CPAchecker-conf/myCPA-PredAbstract-LIA-fast.properties"),
  "output_dir":(_tmp_dir_g + "/proof")}
basic_analyzer.set_paths(options)

# Register available analyzers
basic_analyzer.AnalysisResultFactory.add_factory("CPA", CPA_Factory)

proof_report.set_template_path(_abs_path("./template.graphml"))

def run(design_file, out_dir):
  try:
    program = Program(design_file)
    result = overview.run( program )
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    out_dir = tempfile.mkdtemp(prefix="CPArec-proof-", dir=out_dir)

    if result == "Error": # TODO Produce real witness
      result.get_function_start_exit_trace()
      proof = ErrorProof(program, result)
      proof.print_witness(out_dir + "/witness.graphml")


    shutil.move(_tmp_dir_g + "/proof", out_dir)
    shutil.move(_tmp_dir_g + "/transformed.c", out_dir)
    print ("")
    print ('Proof for "' + str(result) + '" can be found at "' + out_dir + '"')
  except RuntimeError:
    result = 'Unknown'

  shutil.rmtree(_tmp_dir_g, ignore_errors=True)

  return result
