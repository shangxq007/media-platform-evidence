import subprocess, sys, json, pathlib
out=pathlib.Path(__file__).parent
name=sys.argv[1]
assert not (out/(name+'.log')).exists()
command=['node_modules/.bin/vitest','run','--configLoader','runner','--no-cache','--reporter=json','--outputFile='+str(out/(name+'.json'))]+sys.argv[2:]
(out/(name+'.command.json')).write_text(json.dumps(command))
with (out/(name+'.log')).open('w') as log:
 result=subprocess.run(command,cwd='/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend',stdout=log,stderr=subprocess.STDOUT)
(out/(name+'.exit')).write_text(str(result.returncode)+'\n')
print(name, 'exit', result.returncode)
if (out/(name+'.json')).exists():
 data=json.loads((out/(name+'.json')).read_text());print({k:data.get(k) for k in ['numTotalTests','numPassedTests','numFailedTests','numPendingTests']})
 for suite in data.get('testResults',[]):
  for test in suite.get('assertionResults',[]):
   if test['status']=='failed':print(test['fullName'], '\n'.join(test['failureMessages'])[:1500])
else:print((out/(name+'.log')).read_text()[-2000:])
