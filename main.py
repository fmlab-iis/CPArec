import sys
import argparse

sys.dont_write_bytecode=True

import engine

def main():
  args = vars( parse_command_line() )

  design_file = args['program']
  output_dir = args['output']
  proof = engine.run(design_file, output_dir)

  # Simple mapping for SVCOMP
  if proof == 'Pass':
    result = "TRUE"
  elif proof == 'Error':
    result = "FALSE"
  else:
    result = 'UNKNOWN'

  print ("")
  print ("Verification Result: " + result)
  print ("")

  return 0

def parse_command_line():
  # TODO More arguments to define
  parser = argparse.ArgumentParser(
    description='CPArec, verifying recursive C programs via CPAchecker'
  )
  parser.add_argument(
    '--spec',
    metavar="filename.prp", type=file,
    help="Property Specification"
  )
  parser.add_argument(
    '-o', '--output',
    metavar="output_dir/", # TODO Add action to chek if it is a directory
    default="./",
    help="Output directory for proof"
  )
  parser.add_argument(
    'program',
    metavar="program.c", # TODO type=file,
    help="C program to be analyzed"
  )
  return parser.parse_args()

if __name__ == "__main__":
    sys.exit( main() )
