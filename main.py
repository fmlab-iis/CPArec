import sys
sys.dont_write_bytecode=True

#Add paths for external python packages
import engine

design_file = sys.argv[1]
proof = engine.run(design_file)

# Simple mapping for SVCOMP
if proof == 'Pass':
  result = "TRUE"
elif proof == 'Error':
  result = "FALSE"
else:
  result = 'UNKNOWN'

print ("Verification Result: " + result)
print ("")

