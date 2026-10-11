import {bundle} from '@remotion/bundler';
import {selectComposition,renderMedia,renderStill} from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';
const browserExecutable=process.env.CHROME_EXECUTABLE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const serveUrl=await bundle({entryPoint:path.resolve('src/index.tsx'),publicDir:path.resolve('public'),onProgress:p=>{if(p===100)console.log('Composition bundled.')}});
const composition=await selectComposition({serveUrl,id:'TaxReadyCinematic',browserExecutable});
fs.mkdirSync('review',{recursive:true});
if(process.argv.includes('--stills')){
 for(const frame of [150,480,840,1200,1680,2190,2670,3120,3420])await renderStill({serveUrl,composition,output:`review/frame-${frame}.png`,frame,browserExecutable});
 console.log('Nine scene review frames rendered.');
}else{
 let last=-1;await renderMedia({serveUrl,composition,codec:'h264',audioCodec:'aac',crf:18,pixelFormat:'yuv420p',frameRange:process.argv.includes('--test')?[660,750]:undefined,outputLocation:process.argv.includes('--test')?'review/seek-test.mp4':'TaxReady_AI_Cinematic_Demo.mp4',browserExecutable,concurrency:2,offthreadVideoCacheSizeInBytes:268435456,mediaCacheSizeInBytes:134217728,chromiumOptions:{gl:'angle'},onProgress:p=>{const n=Math.floor(p.progress*100);if(n>=last+5){last=n;console.log(`Render ${n}% (${p.renderedFrames}/3600 frames)`);}}});
 console.log('Final MP4 rendered.');
}
