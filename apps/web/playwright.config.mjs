import { defineConfig } from '@playwright/test';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, join, dirname, basename } from 'node:path';
const data=mkdtempSync(join(tmpdir(),'cyberlab-browser-'));
process.on('exit',()=>{try{const target=resolve(data);if(dirname(target)===resolve(tmpdir())&&basename(target).startsWith('cyberlab-browser-'))rmSync(target,{recursive:true,force:true});}catch{}});
export default defineConfig({
  testDir:'./tests', workers:1, fullyParallel:false, timeout:30000,
  use:{baseURL:'http://127.0.0.1:8318',headless:true,trace:'retain-on-failure'},
  webServer:{
    command:`"${process.env.CYBERLAB_PYTHON||'python'}" -m uvicorn cyberlab.main:create_app --factory --host 127.0.0.1 --port 8318 --no-access-log`,
    url:'http://127.0.0.1:8318/api/health', reuseExistingServer:false,timeout:30000,
    env:{...process.env,PYTHONPATH:resolve('../api'),CYBERLAB_DATA:data,CYBERLAB_RUNNER_SOCKET:'',CYBERLAB_STATIC:resolve('dist')},
  },
});
