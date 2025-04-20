import { test, expect } from '@playwright/test';
import path from 'path';

test('full upload and worksheet generation flow', async ({ page }) => {
  // Go to the app
  await page.goto('http://localhost:3000');

  // Upload a sample image
  const filePath = path.resolve(__dirname, 'sample.jpg');
  // Wait for the file input to be attached
  const fileInput = await page.waitForSelector('input[type="file"]', { state: 'attached' });
  await fileInput.setInputFiles(filePath);
  // Wait for preview and upload button, print diagnostics if not found
  try {
    await expect(page.getByRole('button', { name: /hochladen/i })).toBeVisible({ timeout: 7000 });
  } catch (err) {
    // Print the DOM for debugging
    const html = await page.content();
    console.log('DEBUG PAGE HTML:', html);
    throw err;
  }
  await page.getByRole('button', { name: /hochladen/i }).click();

  // Wait for upload success toast
  await expect(page.getByText(/erfolgreich hochgeladen/i)).toBeVisible();

  // Wait for Generate button and click
  await expect(page.getByRole('button', { name: /ähnliche schulaufgabe erstellen/i })).toBeVisible();
  await page.getByRole('button', { name: /ähnliche schulaufgabe erstellen/i }).click();

  // Wait for LaTeX preview and PDF download button
  await expect(page.getByText(/Aufgabe erfolgreich generiert/i)).toBeVisible();
  await expect(page.getByRole('link', { name: /pdf herunterladen/i })).toBeVisible();
}); 