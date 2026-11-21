const test=require('node:test');
const assert=require('node:assert/strict');
const {PROVIDERS,publicHttps,allowedTopLevel,isLocalApp,layout}=require('../policy.cjs');

test('official providers are fixed, no arbitrary navigation',()=>{
  assert.equal(Object.keys(PROVIDERS).length,4);
  assert(allowedTopLevel('chatgpt','https://chatgpt.com/'));
  assert(allowedTopLevel('claude','https://claude.ai/new'));
  assert(!allowedTopLevel('chatgpt','https://chatgpt.com.evil.test/'));
  assert(!allowedTopLevel('unknown','https://chatgpt.com/'));
});
test('remote views cannot access local backend or unsafe protocols',()=>{
  for(const url of ['http://127.0.0.1:8765/','https://127.0.0.1/','https://[::1]/','https://localhost/','https://machine.local/','file:///tmp/test','javascript:alert(1)','https://user:password@chatgpt.com/'])assert.equal(publicHttps(url),false,url);
  assert(publicHttps('https://cdn.example.com/'));assert(publicHttps('wss://cdn.example.com/',true));
});
test('local IPC accepts only exact origin',()=>{
  assert(isLocalApp('http://127.0.0.1:8765/path','http://127.0.0.1:8765'));
  assert(!isLocalApp('http://127.0.0.1:8766/','http://127.0.0.1:8765'));
  assert(!isLocalApp('https://chatgpt.com/','http://127.0.0.1:8765'));
});
test('desktop layout has contiguous non-overlapping views',()=>{
  for(const count of [0,1,2]){const r=layout(1440,900,count);assert.equal(r.remote.length,count);let x=r.local.width;for(const b of r.remote){assert.equal(b.x,x);assert(b.width>=350);x+=b.width;}assert.equal(x,1440);}
});
