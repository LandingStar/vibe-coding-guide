// @ts-check
import { chromium } from 'playwright';
import { readdirSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');
const inputDir = join(projectRoot, 'output', 'monitoring-screenshots');
const screenshotDir = join(projectRoot, 'output', 'monitoring-screenshots');

const htmlFiles = readdirSync(inputDir).filter(f => f.endsWith('.html')).sort();

async function main() {
    const browser = await chromium.launch();

    for (const file of htmlFiles) {
        const filePath = join(inputDir, file);
        const name = basename(file, '.html');

        // Determine viewport width from filename
        const widthMatch = name.match(/(\d+)px$/);
        const width = widthMatch ? parseInt(widthMatch[1], 10) : 1200;

        const page = await browser.newPage({
            viewport: { width, height: 800 },
        });

        await page.goto(`file://${filePath}`, { waitUntil: 'networkidle' });
        await page.waitForTimeout(500);

        const screenshotPath = join(screenshotDir, `${name}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(`Screenshot: ${screenshotPath}`);

        await page.close();
    }

    await browser.close();
    console.log('Done.');
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
