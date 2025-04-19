import { test, expect } from '@playwright/test';
import path from 'path';

test('full upload and worksheet generation flow', async ({ page }) => {
  // Go to the app
  await page.goto('http://localhost:3000');

  // Upload a sample image
  const filePath = path.resolve(__dirname, '../../backend/tests/sample.jpg');
  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.getByText(/drag & drop/i).click();
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles(filePath);

  // Wait for preview and upload button
  await expect(page.getByRole('button', { name: /upload/i })).toBeVisible();
  await page.getByRole('button', { name: /upload/i }).click();

  // Wait for upload success toast
  await expect(page.getByText(/erfolgreich hochgeladen/i)).toBeVisible();

  // Wait for Generate button and click
  await expect(page.getByRole('button', { name: /generate/i })).toBeVisible();
  await page.getByRole('button', { name: /generate/i }).click();

  // Wait for LaTeX preview and PDF download button
  await expect(page.getByText(/Aufgabe erfolgreich generiert/i)).toBeVisible();
  await expect(page.getByRole('link', { name: /pdf herunterladen/i })).toBeVisible();
}); 