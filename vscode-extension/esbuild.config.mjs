// @ts-check
import * as esbuild from 'esbuild';
import { readdirSync, rmSync } from 'node:fs';
import path from 'node:path';

const production = process.argv.includes('--production');
const watch = process.argv.includes('--watch');
const testEntryPoints = readdirSync('src/test', { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.ts'))
    .map((entry) => path.join('src/test', entry.name));
const electronTestEntryPoints = readdirSync('src/electron-test/suite', { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.ts'))
    .map((entry) => path.join('src/electron-test/suite', entry.name));

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
    entryPoints: {
        progressGraphV2Engine: 'src/webviews/progressGraphV2Engine.ts',
        localWorkTrajectory: 'src/webviews/localWorkTrajectory.tsx',
        knowledgeGraphForceWorker: 'node_modules/@note-web/knowledge-graph-engine/src/layout/force-worker.js',
    },
    bundle: true,
    outdir: 'dist/webviews',
    format: 'iife',
    platform: 'browser',
    target: 'es2022',
    sourcemap: !production,
    minify: production,
    treeShaking: true,
};

/** @type {esbuild.BuildOptions} */
const testBuildOptions = {
    entryPoints: testEntryPoints,
    bundle: true,
    outdir: 'dist/test',
    format: 'cjs',
    platform: 'node',
    target: 'node20',
    sourcemap: !production,
    minify: false,
    treeShaking: true,
    external: ['vscode'],
};

/** @type {esbuild.BuildOptions} */
const electronTestBuildOptions = {
    entryPoints: electronTestEntryPoints,
    bundle: true,
    outdir: 'dist/electron-test/suite',
    format: 'cjs',
    platform: 'node',
    target: 'node20',
    sourcemap: !production,
    minify: false,
    treeShaking: true,
    external: ['vscode'],
};

async function main() {
    if (watch) {
        const contexts = await Promise.all([
            esbuild.context(extensionBuildOptions),
            esbuild.context(webviewBuildOptions),
            ...(testEntryPoints.length > 0 ? [esbuild.context(testBuildOptions)] : []),
            ...(electronTestEntryPoints.length > 0 ? [esbuild.context(electronTestBuildOptions)] : []),
        ]);
        await Promise.all(contexts.map((context) => context.watch()));
        console.log('[watch] build started');
    } else {
        rmSync('dist', { recursive: true, force: true });
        await Promise.all([
            esbuild.build(extensionBuildOptions),
            esbuild.build(webviewBuildOptions),
            ...(testEntryPoints.length > 0 ? [esbuild.build(testBuildOptions)] : []),
            ...(electronTestEntryPoints.length > 0 ? [esbuild.build(electronTestBuildOptions)] : []),
        ]);
        console.log('build complete');
    }
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
