import subprocess
import re

__tran_path_g = ""
__output_path_g = ""
__count_g = 0


def set_tran_path(path):
  global __tran_path_g
  __tran_path_g = path
def set_output_path(path):
  global __output_path_g 
  __output_path_g = path

def _call_tran(p_args, p_input):
  global __tran_path_g, __output_path_g, __count_g
  assert __tran_path_g != "" and __output_path_g != "" 
  args = [__tran_path_g]
  args.extend(p_args)

  # Insert definition of assume/assert function
  args.append("-i")
  # Set Output File
  output_name = __output_path_g + "/tmp"+str(__count_g)+".c"
  __count_g = __count_g + 1
  args.extend(["-o", output_name])
  # Set Input File
  args.append(p_input)
  out_str = subprocess.check_output(args, stderr=subprocess.STDOUT)
  # TODO logging.info(out_str)

  return output_name

class Program:
  def __init__(self, file_name):
    self.__input = file_name
    self.__real_file = None
    self.__args = []
    # One Return Location
    self.__args.append("-r")
    # Use unique variable names as actual parameters
    self.__args.append("-s")

    self.__rec_funcs = self.__find_recursive_funcs()
    self.__uwd_funcs = []

  def __find_recursive_funcs(self):
    #TODO Refine, this workaround is not efficient
    p_args = ["-l", "-r", "-s", "-u"]
    design_name = _call_tran(p_args, self.__input)
    func_name_set = set()
    func_list = []
    with open(design_name, "r") as design_file:
      for line in design_file:
        pattern = r"( +)// (?P<name>\w+);((?P<ret>\w+)=(?P<rcv>\w+))?;(?P<para>\w+=\w+(,\w+=\w+)*)?$"
        m = re.match(pattern, line)
        if m:
          func_name = m.group("name")
          if func_name in func_name_set:
            continue
          func_name_set.add( func_name )
          ret = m.group("ret")
          paras = m.group("para")
          if paras:
            paras = paras.split(',')
            paras = map(lambda x: (x.split('='))[0], paras)
          f = Function(func_name, ret, paras)
          func_list.append(f)
    design_file.close()

    return func_list

  def is_recursive(self):
    return len(self.__rec_funcs) != 0

  def get_input(self):
    return self.__input
  def get_recursive_funcs(self):
    return self.__rec_funcs
  def get_unwound_funcs(self):
    return self.__uwd_funcs

  def __duplicate_func(self, func, new_func):
    self.__args.extend(["-d", func, new_func])

  def __replace_calls(self, func, old_call, new_call):
    self.__args.extend(["-R", func, old_call, new_call])

# TODO Find a way to keep relation between old and new recursive function
# TODO Avoid naming conflict caused by adding suffix _0
  def unwind(self, k):
    old_rec_funcs = self.__rec_funcs
    new_rec_funcs = []

    # Duplicate functions first
    for i in range(k):
      for func in old_rec_funcs:
        name = func.get_name()
        new_func_name = name + '_' + str(i)
        # Always duplicate the same original function
        self.__duplicate_func(name, new_func_name)
    # Replace function calls in duplicated functions
    for i in range(k + 1):
      for func in old_rec_funcs:
        if i < k:
          new_func_name = func.get_name() + '_' + str(i)
        else:
          new_func_name = func.get_name()
        for old_call in old_rec_funcs:
          old_call_name = old_call.get_name()
          if i > 0:
            new_call_name = old_call_name + '_' + str(i-1)
          else:
            new_call_name = old_call_name + '_0'
            new_call = old_call.duplicate(new_call_name)
            new_rec_funcs.append(new_call)
          # Replace calls in the duplicated function
          self.__replace_calls(new_func_name, old_call_name, new_call_name)

    # Update the recursive functions in unwound program
    self.__uwd_funcs = self.__rec_funcs
    self.__rec_funcs = new_rec_funcs

  def instantiate_summary(self, func_name, pre, post):
    self.__args.extend(["-m", func_name, pre, post])
  def assert_summary(self, func_name, pre, post):
    self.__args.extend(["-t", func_name, pre, post])

# TODO A more robust way to know if a file is really created
  def create_file(self):
    if not self.__real_file:
      # Do the transformation only when needed
      self.__real_file =_call_tran(self.__args, self.__input)
    
    return self.__real_file 

class Function(object):
  def __init__(self, name, ret, paras):
    self.__name = name
    self.__ret  = ret
    self.__para_list = []
    if paras: self.__para_list.extend(paras)

  def add_scope(self, var):
    return self.__name + "::" + var

  def __str__(self):
    return self.__name
  def __repr__(self):
    return self.__name

  def get_name(self):
    return self.__name
  def get_return_parameters(self):
    return [self.__ret]
  def get_input_parameters(self):
    return self.__para_list
  def get_all_parameters_with_scope(self):
    inputs = map(self.add_scope, self.__para_list)
    return self.get_return_parameters() + inputs

  def duplicate(self, new_name):
    return Function(
             new_name,
             self.__ret,
             self.__para_list)

# TODO This is because C has no overloading
  def __eq__(self, other):
    return self.__name == other.__name

  def __str__(self):
    s = ""
    if self.__ret: s += self.__ret + "="
    s += self.__name + "("
    for p in self.__para_list:
      s += p + ","
    s = s[:-1] + ")"
    return s
