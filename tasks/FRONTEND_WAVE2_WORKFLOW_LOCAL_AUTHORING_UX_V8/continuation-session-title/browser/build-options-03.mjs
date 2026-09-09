// Merge with actual DEFAULT Vite config; do not pass configFile:false.
import path from 'node:path'
import {fileURLToPath} from 'node:url'
const P=path.dirname(fileURLToPath(import.meta.url))
const S=path.resolve(P,'../validation-01/snapshot/frontend')
const H=path.join(P,'fixture-host')
export const output=path.resolve(P,'./build-03')
export const opts={resolve:{dedupe:['react','react-dom','@tanstack/react-query','@tanstack/query-core','@tanstack/react-router','@tanstack/router-core','@tanstack/react-store','@tanstack/store']},configLoader:'bundle',plugins:[{
 name:'explicit-isolated-workflow-sdk-boundary',enforce:'pre',
 resolveId(source,importer) {
  if(source==='@/auth/oidcConfig')return path.join(H,'oidc-config.ts')
  if(source==='oidc-client-ts')return path.join(H,'sdk.ts')
  if(importer && source.startsWith('.') && path.resolve(path.dirname(importer.split('?')[0]),source).replace(/\.ts$/,'')===path.join(S,'src/auth/oidcConfig'))return path.join(H,'oidc-config.ts')
  if(source.replace(/\.ts$/,'')===path.join(S,'src/auth/oidcConfig'))return path.join(H,'oidc-config.ts')
 }
}],build:{outDir:output,emptyOutDir:false,manifest:true,rollupOptions:{input:{application:path.join(S,'index.html'),fixture:path.join(H,'entry.tsx')}}}}
