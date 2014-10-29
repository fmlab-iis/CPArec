import sys
sys.dont_write_bytecode=True

#Add paths for external python packages
import engine

design_file = sys.argv[1]
try:
  proof = engine.run(design_file)
except RuntimeError:
  proof = 'Unknown'

if proof == 'Pass':
  result = "TRUE"
elif proof == 'Error':
  result = "FALSE"
else:
  result = 'UNKNOWN'

print ("Verification Result: " + result)
print ("")

