import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';import fs from 'node:fs';import path from 'node:path';
const root=path.resolve(process.argv[2]),outDir=path.resolve(process.argv[3]);const require=createRequire(path.join(root,'package.json'));
const {resolveConfig}=await import(pathToFileURL(require.resolve('vite')).href);
const c=await resolveConfig({root,build:{outDir}},'build','production','production');
if(path.resolve(c.build.outDir)!==outDir||c.build.emptyOutDir!==true||c.mode!=='production'||!c.isProduction)throw new Error('UNEXPECTED_RESOLVED_BUILD_BOUNDARY');
fs.writeFileSync(process.argv[4],JSON.stringify({root:c.root,configFile:c.configFile,outDir:c.build.outDir,emptyOutDir:c.build.emptyOutDir,mode:c.mode,isProduction:c.isProduction,publicDir:c.publicDir},null,2)+'\n',{flag:'wx'});
