import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('new tutorials link to their lab and the catalog supports filters and search',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('.new-lesson-grid button')).toHaveCount(8);
  await page.locator('.new-lesson-grid button').filter({hasText:'XSS'}).click();
  await page.getByRole('button',{name:'İlgili labı aç'}).click();
  await expect(page.locator('.lab-card.expanded h2')).toContainText('HTML');
  await expect(page.locator('.lab-card')).toHaveCount(21);
  await page.getByRole('combobox',{name:'Lab koleksiyonu'}).selectOption('yeni');
  await expect(page.locator('.lab-card')).toHaveCount(8);
  await page.getByLabel('Lab ara',{exact:true}).fill('JWT');
  await expect(page.locator('.lab-card')).toHaveCount(1);
  await expect(page.locator('.lab-card h2')).toContainText('tokenı');
  await page.getByLabel('Lab ara',{exact:true}).fill('olmayan-konu');
  await expect(page.getByRole('status')).toContainText('bulunamadı');
  await page.getByRole('button',{name:'Tüm labları göster'}).click();
  await expect(page.locator('.lab-card')).toHaveCount(21);
  expect(errors).toEqual([]);
});

for(const width of [1366,390]){
  test(`keyboard, overflow and WCAG audit at ${width}px`,async({page})=>{
    await page.setViewportSize({width,height:900});
    await page.goto('/');
    await expect(page.locator('.new-lesson-grid button')).toHaveCount(8);
    await page.keyboard.press('Tab');
    await expect(page.getByRole('link',{name:'İçeriğe geç'})).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('#main-content')).toBeFocused();
    for(const destination of ['Genel bakış','Öğrenme yolu','Bulmacalar','Laboratuvar']){
      await page.locator('.range-nav').filter({hasText:destination}).click();
      await expect(page.locator('.lesson-body .metin, .bulmaca, .lab-card, .hero').first()).toBeVisible();
      const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
      expect(results.violations.map(v=>({id:v.id,description:v.description,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);
      expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
    }
  });
}
