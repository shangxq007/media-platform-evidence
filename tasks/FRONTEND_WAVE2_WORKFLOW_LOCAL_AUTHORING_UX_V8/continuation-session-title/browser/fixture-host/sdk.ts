// Explicit isolated SDK transport/events; actual installed User semantics.
import { User } from '/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot/frontend/node_modules/oidc-client-ts/dist/esm/oidc-client-ts.js'
export { User }
let active=false
export function activateFixture(){if(location.hostname!=='127.0.0.1'||new URLSearchParams(location.search).get('workflowFixture')!=='1')throw Error('Opt-in required');active=true}
export function isFixtureActive(){return active}
const names=['UserLoaded','UserUnloaded','AccessTokenExpired','UserSignedIn','UserSignedOut','UserSessionChanged']
const listeners=new Map(names.map(n=>[n,new Set<any>()]));const retained:any[]=[]
export const sdkLog:any[]=[]
let serial=0
function make(overrides:any={}){return new User({access_token:'NON_CREDENTIAL_SIMULATION_'+(++serial),token_type:'Bearer',scope:'openid profile',expires_at:Math.floor(Date.now()/1000)+3600+serial,profile:{iss:'https://invalid.invalid/',aud:'EXPLICIT-NON-CREDENTIAL-FIXTURE',sub:'simulated-A',sid:'simulated-session-A',iat:1,exp:Math.floor(Date.now()/1000)+3600,...overrides}})}
let current:User|null=make();let old=current;let deferNext=false;let pending:any;let redirect:any
export function setCurrent(overrides:any={}){old=current;current=make(overrides);sdkLog.push({store:current.profile});return currentInfo()}
export function currentInfo(){return {profile:current?.profile,expired:current?.expired,scopes:current?.scopes}}
export async function emitNative(name:string,payload:any=current){if(!active||!listeners.has(name))throw Error('Inactive/unknown');const callbacks=[...listeners.get(name)!];sdkLog.push({event:name,callbacks:callbacks.length,payload:payload?.profile});if(!callbacks.length)throw Error('Subscription missing');await Promise.all(callbacks.map(fn=>fn(payload)))}
export function emitLoaded(stale=false){return emitNative('UserLoaded',stale?old:current)}
export function deferGetter(){deferNext=true}
export function pendingLoaded(){deferGetter();void emitLoaded();return true}
export function settleGetter(){if(!pending)throw Error('No pending getter');pending();pending=undefined}
export function settleSignout(bad=false){if(!redirect)throw Error('No redirect');redirect(bad);redirect=undefined}
export function replayRetired(){retained.forEach(fn=>fn());return retained.length}
export class WebStorageStateStore{constructor(_options:any){}}
export class UserManager{
 events:Record<string,any>={}
 constructor(_settings:any){if(!active)throw Error('Not active');for(const n of names){this.events['add'+n]=(f:any)=>{listeners.get(n)!.add(f);sdkLog.push({add:n})};this.events['remove'+n]=(f:any)=>{listeners.get(n)!.delete(f);retained.push(f);sdkLog.push({remove:n})}}}
 getUser(){const captured=current;sdkLog.push({getUser:true,profile:captured?.profile,deferred:deferNext});if(!deferNext)return Promise.resolve(captured);deferNext=false;return new Promise<User|null>(resolve=>{pending=()=>resolve(captured)})}
 signoutRedirect(){return new Promise<void>((resolve,reject)=>{redirect=(bad:boolean)=>bad?reject(Error('SIMULATED redirect rejected')):resolve()})}
 signinRedirect(){throw Error('Forbidden')}
 signinRedirectCallback(){throw Error('Forbidden')}
}
