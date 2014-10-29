# TODO All interfaces provided are buggy

def isSMTLibCommand(line):
  return line.startswith("(")

def isDefineFunction(line):
  return line.startswith("(define-fun")

def isAssert(line):
  return line.startswith("(assert")

def getDefineFunctionName(line):
  return (line.split(" ", 2))[1]

def getAssertName(line):
  line = (line).strip('()\n')
  return (line.split(" "))[1]

def tokenize(line_str):
  assert line_str[0] == '(' and line_str[-1] == ')'
  pos = 1
  items_begin = 1
  top_list = []
  stack_of_lists = []
  while pos < len(line_str)-1:
    if line_str[pos] == '(' :
      if items_begin != pos:
        top_list.extend(((line_str[items_begin:pos]).strip()).split())
      stack_of_lists.append(top_list)
      top_list = []
      items_begin = pos + 1
    elif line_str[pos] == ")":
      if items_begin != pos:
        top_list.extend(((line_str[items_begin:pos]).strip()).split())
      tmp_list = stack_of_lists.pop()
      tmp_list.append(top_list)
      top_list = tmp_list
      items_begin = pos + 1
    pos = pos + 1

  assert len(stack_of_lists) == 0

  return top_list

def toCOperator(operator):
  if type(operator)==list:
    return "{"+str(operator)+"}"
  assert operator in set(["not", "and", "or", "=", ">=", "<=", ">", "<", "+", "-", "*", "div", "mod", "to_real"])
  op_dict = {"not":"not",
             "and":"and", 
             "or" :"or",
             "="  :"=",
             "mod":"%",
             "div":"/",
             "to_real":""}
  # FIXME 
  assert operator != "mod"
  if(operator in op_dict):
    return op_dict[operator]
  return operator
