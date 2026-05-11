// @ts-check
import * as esbuild from 'esbuild';

const production = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

/** @type {esbuild.BuildOptions} */
const extensionBuildOptions = {
    entryPoints: ['src/extension.ts'],
    bundle: true,
    outfile: 'dist/extension.js',
    external: ['vscode'],
    format: 'cjs',
    platform: 'node',
    target: 'node20',
    sourcemap: !production,
    minify: production,
    treeShaking: true,
};

/** @type {esbuild.BuildOptions} */
const webviewBuildOptions = {
    entryPoints: ['src/webviews/progressGraphV2G6.ts'],
    bundle: true,
    outdir: 'dist/webviews',
    format: 'iife',
    platform: 'browser',
    target: 'es2022',
    sourcemap: !production,
    minify: production,
    treeShaking: true,
};

async function main() {
    if (watch) {
        const extensionContext = await esbuild.context(extensionBuildOptions);
        const webviewContext = await esbuild.context(webviewBuildOptions);
        await Promise.all([extensionContext.watch(), webviewContext.watch()]);
        console.log('[watch] build started');
    } else {
        await Promise.all([
            esbuild.build(extensionBuildOptions),
            esbuild.build(webviewBuildOptions),
        ]);
        console.log('build complete');
    }
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
