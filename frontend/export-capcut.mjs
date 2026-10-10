import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const folder=path.resolve('../presentation/capcut-kit');await fs.mkdir(folder,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1920,height:1080}});
await page.goto(pathToFileURL(path.resolve('../presentation/arjun-story.html')).href);
const names=['01-tax-season','02-document-confusion','03-private-workspace','04-review-fields','05-tds-difference','06-readiness-dashboard','07-confidence-report'];
for(let i=0;i<7;i++){
 const data=await page.evaluate(index=>{c.width=1920;c.height=1080;g.setTransform(1.5,0,0,1.5,0,0);timeline=[0,20,40,60,80,100,120];D=140;draw(index*20+10);return c.toDataURL('image/png').split(',')[1]},i);
 await fs.writeFile(path.join(folder,names[i]+'.png'),Buffer.from(data,'base64'));
}
const base='http://127.0.0.1:5173';
await page.goto(base+'/');await page.getByRole('link',{name:'Explore demo'}).click();await page.getByRole('button',{name:'Enter demo workspace'}).click();
await page.getByRole('heading',{name:'Welcome back, Sammer.'}).waitFor();
const token=await page.evaluate(()=>sessionStorage.getItem('taxready_token'));
const headers={Authorization:'Bearer '+token};
const documents=await (await page.request.get(base+'/api/v1/documents',{headers})).json();
for(const d of documents){const response=await page.request.patch(base+'/api/v1/documents/'+d.id+'/verify',{headers,data:{fields:d.fields.map(f=>({id:f.id,value:f.value,verified:true}))}});if(!response.ok())throw new Error('Could not review synthetic record');}
await page.reload();await page.getByRole('heading',{name:'Welcome back, Sammer.'}).waitFor();
await page.waitForFunction(()=>document.querySelector('.readiness-ring strong')?.textContent==='59%');
async function shot(name){await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:path.join(folder,name+'.png'),animations:'disabled'});}
await shot('08-real-app-dashboard');
await page.getByRole('link',{name:'Documents',exact:true}).click();await page.getByRole('link',{name:/form16.pdf/}).waitFor();await shot('09-real-app-documents');
await page.getByRole('link',{name:/form16.pdf/}).click();await page.getByRole('textbox',{name:'Gross Salary'}).waitFor();await page.locator('.source-card iframe').waitFor();await shot('10-real-app-review');
await page.getByRole('link',{name:'Verification',exact:true}).click();await page.getByRole('heading',{name:'TDS discrepancy detected'}).waitFor();await shot('11-real-app-findings');
await page.getByRole('link',{name:'Report center',exact:true}).click();await page.getByRole('button',{name:'Generate report',exact:true}).click();await page.getByRole('button',{name:'View snapshot'}).first().waitFor();await shot('12-real-app-reports');
await page.getByRole('button',{name:'View snapshot'}).first().click();await page.getByRole('heading',{name:'Saved report snapshot'}).waitFor();await shot('13-report-snapshot');await page.getByRole('button',{name:'Close dialog'}).click();
await page.getByRole('link',{name:/AI assistant/}).click();await page.getByRole('button',{name:'Why does my TDS not match?'}).first().click();await page.locator('.chat-sources a').first().waitFor();await shot('14-ai-assistant-answer');
await page.getByRole('button',{name:'Assistant settings',exact:true}).click();await page.getByLabel('Answer provider').selectOption('openai');await shot('15-own-api-key-settings');await page.getByRole('button',{name:'Close dialog'}).click();
await page.getByRole('link',{name:'Privacy & activity',exact:true}).click();await page.getByRole('button',{name:'Export workspace JSON'}).waitFor();await shot('16-privacy-and-activity');
await page.getByRole('link',{name:'My checklist',exact:true}).click();await page.getByRole('heading',{name:'3 of 5 items complete'}).waitFor();await shot('17-personalized-checklist');
await page.getByRole('link',{name:'Financial profile',exact:true}).click();await page.getByRole('textbox',{name:'Your name'}).waitFor();await shot('18-financial-profile');
await page.getByRole('link',{name:'Overview',exact:true}).click();await page.getByRole('heading',{name:'Welcome back, Sammer.'}).waitFor();await page.getByRole('button',{name:'Use dark theme'}).click();await shot('19-dark-dashboard');await page.getByRole('button',{name:'Use light theme'}).click();
await page.getByRole('button',{name:'Beginner tour',exact:true}).click();await page.getByRole('combobox',{name:'Tour chapter'}).selectOption('Overview');await page.getByRole('heading',{name:'Your personal dashboard',exact:true}).waitFor();await page.waitForTimeout(800);await shot('20-moving-beginner-guide');
await page.getByRole('button',{name:'Next',exact:true}).click();await page.getByRole('heading',{name:'Year, demo mode, and theme',exact:true}).waitFor();await page.waitForTimeout(800);await shot('21-guide-next-position');await page.getByRole('button',{name:'Close beginner tour'}).click();
await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'Beginner tour',exact:true}).click();await page.getByRole('combobox',{name:'Tour chapter'}).selectOption('Overview');await page.waitForTimeout(800);await shot('22-mobile-guide');
await browser.close();console.log('Updated kit: 7 story scenes and 15 current app screenshots.');
