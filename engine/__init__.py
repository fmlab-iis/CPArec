import os
import tempfile
import shutil

from transform_manager import Program
import overview

import basic_analyzer
import redlog_manager as rl_mgr

from cpa_checker import CPA_Factory

_this_dir_g = os.path.dirname(__file__)

def _abs_path(rel_path):
  global _this_dir_g
  return os.path.join(_this_dir_g, rel_path)

_tmp_dir_g = tempfile.mkdtemp(dir = _abs_path("../var/"))

# TODO better contorl of configuration
transform_manager.set_tran_path(_abs_path("../tran/tran.native"))
transform_manager.set_output_path(_tmp_dir_g)

rl_mgr.setExePath(_abs_path("../ext_quantifier/reduce/reduce"))
rl_mgr.setScriptPath(_abs_path(_tmp_dir_g + "/rl_script"))
rl_mgr.setOutputPath(_abs_path(_tmp_dir_g + "/rl_summary"))

options = {
  "bin_file"  :_abs_path("../ext_analyzer/CPAchecker-1.3.4-unix/scripts/cpa.sh"),
  "conf_file" :_abs_path("../ext_analyzer/CPAchecker-conf/UsedConfiguration.properties"),
  "output_dir":_abs_path(_tmp_dir_g + "/proof")}
basic_analyzer.set_paths(options)

# Register available analyzers
basic_analyzer.AnalysisResultFactory.add_factory("CPA", CPA_Factory)

def run(design_file):
  try:
    result = overview.run( Program(design_file) )
    if result == 'Error':
      # TODO Move error report to Error class
      print ((" Error Witness ").center(70, '='))
      print ("Values changes of variables in main() and global variables")
      assignment = result.get_variable_assignment()
      for var, values in assignment.iteritems():
        if var.startswith('main::') or not '::' in var:
          print (var + ': ' + str(values))
  except RuntimeError:
    result = 'Unknown'

  shutil.rmtree(_tmp_dir_g, ignore_errors=True)

  return result
