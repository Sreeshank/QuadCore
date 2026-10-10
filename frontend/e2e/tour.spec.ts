import {test,expect} from '@playwright/test';
test('beginner tour covers every chapter without changing records and works on mobile',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await page.getByRole('link',{name:'Explore demo'}).click();await page.getByRole('button',{name:'Enter demo workspace'}).click();
 await expect(page.getByRole('heading',{name:'Welcome back, Sammer.'})).toBeVisible();
 const writes:string[]=[];page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method()))writes.push(r.method()+' '+r.url());});
 await page.getByRole('button',{name:'Beginner tour',exact:true}).click();
 const panel=page.getByRole('dialog',{name:'Welcome to your beginner tour'});
 await expect(panel).toBeVisible();await expect.poll(()=>panel.evaluate(el=>getComputedStyle(el).transitionProperty)).toContain('left');await expect(panel.getByRole('button',{name:'Back',exact:true})).toBeDisabled();
 for(let i=0;i<32;i++){
  const dialog=page.locator('.tour-panel');await dialog.getByRole('button',{name:'Next',exact:true}).click();
  await expect(dialog.getByRole('progressbar')).toHaveAttribute('aria-valuenow',String(i+2));
  if(i===3){await expect.poll(async()=>{const b=await dialog.boundingBox();return !!b&&b.y>=0&&b.y+b.height<=page.viewportSize()!.height+1;}).toBe(true);}
  if(i===3)await page.screenshot({path:'test-results/beginner-tour-desktop.png'});
 }
 await expect(page.getByRole('heading',{name:'You are ready to explore',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Finish',exact:true}).click();await expect(page.locator('.tour-panel')).toHaveCount(0);await expect(page.locator('.tour-highlight')).toHaveCount(0);
 expect(writes).toEqual([]);
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});
 await page.getByRole('button',{name:'Beginner tour',exact:true}).click();
 await page.getByRole('combobox',{name:'Tour chapter'}).selectOption('Documents');
 await expect(page).toHaveURL(/\/app\/documents$/);await expect(page.locator('.upload-zone')).toHaveClass(/tour-highlight/);
 await page.getByRole('button',{name:'Back',exact:true}).click();await expect(page.getByRole('combobox',{name:'Tour chapter'})).toHaveValue('Overview');
 const bounds=await page.locator('.tour-panel').boundingBox();expect(bounds!.x).toBeGreaterThanOrEqual(0);expect(bounds!.x+bounds!.width).toBeLessThanOrEqual(391);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/beginner-tour-mobile.png'});
 await page.keyboard.press('Escape');await expect(page.locator('.tour-panel')).toHaveCount(0);await expect(page.getByRole('button',{name:'Beginner tour',exact:true})).toBeFocused();
 expect(errors).toEqual([]);
});
