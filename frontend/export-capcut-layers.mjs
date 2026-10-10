import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';import {pathToFileURL} from 'node:url';
const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage();await page.goto(pathToFileURL(path.resolve('../presentation/arjun-story.html')).href);
for(const [name,kind] of [['arjun-worried',0],['arjun-happy',1],['document-form16',2],['document-form26as',3],['document-bank',4]]){
const data=await page.evaluate(k=>{c.width=600;c.height=600;g.setTransform(2,0,0,2,0,0);g.clearRect(0,0,300,300);if(k<2)person(150,90,k===1);else doc(150,150,['Form 16','Form 26AS','Bank record'][k-2]);return c.toDataURL('image/png').split(',')[1]},kind);await fs.writeFile(path.resolve('../presentation/capcut-kit/'+name+'.png'),Buffer.from(data,'base64'));}
await browser.close();
