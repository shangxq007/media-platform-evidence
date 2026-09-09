import { isFixtureActive } from './sdk'
export const isOidcEnabled = isFixtureActive
export function getOidcSettings() { if(!isFixtureActive())throw Error('Unconfigured');return {issuer:'https://invalid.invalid/',clientId:'EXPLICIT-NON-CREDENTIAL-FIXTURE',redirectUri:'http://127.0.0.1:4198/not-used',scope:'openid'} }
