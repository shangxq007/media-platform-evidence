import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(process.argv[2]);const output=path.resolve(process.argv[3]);
const require=createRequire(path.join(root,'package.json'));
const {createVitest}=await import(pathToFileURL(require.resolve('vitest/node')).href);
const context=await createVitest('test',{root,watch:false,reporters:[],passWithNoTests:false});
const rows=[];
try {
 await context.collect();
 if(context.state.getUnhandledErrors().length)throw new Error('COLLECTION_UNHANDLED_ERRORS');
 for(const file of context.state.getFiles()) {
  if(file.result?.errors?.length)throw new Error('COLLECTION_FILE_ERROR');
  const rel=path.relative(path.dirname(root),file.filepath);
  if(rel.startsWith('..')||path.isAbsolute(rel))throw new Error('COLLECTION_FILE_ESCAPE');
  function walk(tasks,ancestors) {
   for(const task of tasks) {
    if(task.type==='suite')walk(task.tasks,[...ancestors,task.name]);
    else if(task.type==='test')rows.push({file:rel,ancestorTitles:ancestors,title:task.name});
    else throw new Error('UNKNOWN_COLLECTED_TASK');
   }
  }
  walk(file.tasks,[]);
 }
 if(!rows.length)throw new Error('EMPTY_COLLECTION');
 rows.sort((a,b)=>Buffer.compare(Buffer.from(JSON.stringify(a)),Buffer.from(JSON.stringify(b))));
 fs.writeFileSync(output,rows.map(x=>JSON.stringify(x)).join('\n')+'\n',{flag:'wx'});
} finally {await context.close();}
