import {test,expect} from '@playwright/test';
test('own-key assistant requires consent, sends request-only key, and clears on leaving',async({page})=>{
 const key='sk-browser-test-dummy-credential';
 await page.goto('/');await page.getByRole('link',{name:'Explore demo'}).click();await page.getByRole('button',{name:'Enter demo workspace'}).click();
 await page.getByRole('link',{name:/AI assistant/}).click();await page.getByRole('button',{name:'Assistant settings',exact:true}).click();
 await page.getByLabel('Answer provider').selectOption('openai');await page.getByLabel('OpenAI API key',{exact:true}).fill(key);
 await expect(page.getByRole('button',{name:'Done',exact:true})).toBeDisabled();
 await page.getByRole('checkbox',{name:/Allow my question/}).check();await page.getByRole('button',{name:'Done',exact:true}).click();
 let called=false;
 await page.route('**/api/v1/assistant/chat',async route=>{
  const r=route.request();const body=r.postDataJSON();expect(body.provider).toBe('openai');expect(body.share_context).toBe(true);expect(r.headers()['x-assistant-api-key']).toBe(key);expect(r.postData()).not.toContain(key);called=true;
  await route.fulfill({json:{answer:'Review your supported source records.',references:[],mode:'openai_user_key',disclaimer:'Preparation guidance.'}});
 });
 await page.getByRole('textbox',{name:'Your question'}).fill('Explain my progress');await page.getByRole('button',{name:'Send message'}).click();
 await expect(page.getByText('Review your supported source records.',{exact:true})).toBeVisible();expect(called).toBe(true);
 const stored=await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}));expect(stored).not.toContain(key);
 await page.getByRole('button',{name:'Assistant settings',exact:true}).click();await page.screenshot({path:'test-results/assistant-key-settings.png',animations:'disabled'});
 await page.getByRole('button',{name:'Clear key & use built-in'}).click();await expect(page.getByLabel('Answer provider')).toHaveValue('builtin');await page.getByRole('button',{name:'Done',exact:true}).click();
 await page.getByRole('button',{name:'Assistant settings',exact:true}).click();await page.getByLabel('Answer provider').selectOption('openai');await page.getByLabel('OpenAI API key',{exact:true}).fill(key);await page.getByRole('checkbox',{name:/Allow my question/}).check();await page.getByRole('button',{name:'Done',exact:true}).click();
 await page.getByRole('link',{name:'Overview',exact:true}).click();await page.getByRole('link',{name:/AI assistant/}).click();
 await page.getByRole('button',{name:'Assistant settings',exact:true}).click();await page.getByLabel('Answer provider').selectOption('openai');await expect(page.getByLabel('OpenAI API key',{exact:true})).toHaveValue('');
 await page.getByRole('button',{name:'Close dialog'}).click();await page.getByRole('link',{name:'Overview',exact:true}).click();await page.getByRole('link',{name:/AI assistant/}).click();await expect(page.getByText('BUILT-IN MODE',{exact:true})).toBeVisible();
});
