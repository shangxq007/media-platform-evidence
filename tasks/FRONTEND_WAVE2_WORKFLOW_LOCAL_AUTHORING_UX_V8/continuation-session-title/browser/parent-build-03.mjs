// Parent-only authorized build entry; preparation author has not executed this.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {opts,output} from './build-options-03.mjs'
const P=path.dirname(fileURLToPath(import.meta.url)),S=path.resolve(P,'../validation-01/snapshot/frontend')
if(process.cwd()!==S)throw Error('Run from final snapshot/frontend')
if(fs.existsSync(output))throw Error('External build output must be new')
const {build,resolveConfig}=await import(pathToFileURL(path.join(S,'node_modules/vite/dist/node/index.js')))
const c=await resolveConfig(opts,'build')
if(path.resolve(c.root,c.build.outDir)!==output)throw Error('Unexpected effective output')
console.log('EFFECTIVE_EXTERNAL_OUTPUT='+output)
await build(opts)
const manifest=JSON.parse(fs.readFileSync(path.join(output,'.vite/manifest.json'),'utf8'))
const fixture=Object.values(manifest).find(x=>x.isEntry&&x.name==='fixture')
if(!fixture)throw Error('Missing explicit fixture entry')
const html=fs.readFileSync(path.join(output,'index.html'),'utf8')
const fixtureHtml=html.replace(/(<script[^>]+src=")([^"]+)(")/,(_,a,b,c)=>a+'/'+fixture.file+c)
if(html===fixtureHtml)throw Error('Missing ordinary module entry')
fs.writeFileSync(path.join(output,'fixture.html'),fixtureHtml)
console.log('EXPLICIT_FIXTURE_ENTRY='+fixture.file)
