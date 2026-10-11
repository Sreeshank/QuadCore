import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import ffmpeg from 'ffmpeg-static';
import ffprobe from 'ffprobe-static';
const scenes=JSON.parse(fs.readFileSync('scenes.json','utf8'));
const run=args=>execFileSync(ffmpeg,['-hide_banner','-loglevel','error','-y',...args],{stdio:'inherit'});
const duration=file=>Number(execFileSync(ffprobe.path,['-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',file],{encoding:'utf8'}).trim());
const captions=[];const inputs=[];const filters=[];let script='TAXREADY AI — CINEMATIC DEMO\nLocal narration: Microsoft David Desktop.\n\n';
for(let i=0;i<scenes.length;i++){
 const s=scenes[i],d=duration(`public/voice/${i}.wav`),available=s.duration-1.5,rate=Math.max(1,d/available);
 run(['-i',`public/voice/${i}.wav`,'-af',`atempo=${rate},aresample=48000,afade=t=in:d=0.035,afade=t=out:st=${d/rate-.08}:d=0.08`,'-ac','1',`public/voice/timed-${i}.wav`]);
 s.voiceStart=s.start+.65;s.voiceDuration=duration(`public/voice/timed-${i}.wav`);s.speechRate=rate;
 inputs.push('-i',`public/voice/timed-${i}.wav`);filters.push(`[${i}:a]adelay=${Math.round(s.voiceStart*1000)}:all=1[a${i}]`);
 const words=s.text.split(/\s+/);for(let k=0;k<words.length;k+=9){const chunk=words.slice(k,k+9);captions.push({start:s.voiceStart+s.voiceDuration*k/words.length,end:s.voiceStart+s.voiceDuration*Math.min(k+9,words.length)/words.length,text:chunk.join(' ')});}
 script+=`${String(i+1).padStart(2,'0')} | ${s.start}–${s.start+s.duration}s | ${s.title}\n${s.text}\n\n`;
}
filters.push(scenes.map((_,i)=>`[a${i}]`).join('')+`amix=inputs=${scenes.length}:normalize=0,apad,atrim=0:120,loudnorm=I=-16:TP=-2:LRA=8[voice]`);
run([...inputs,'-filter_complex',filters.join(';'),'-map','[voice]','-ar','48000','-ac','2','voiceover.wav']);
// Original synthesized score: A minor / F / C / G pads, arpeggios, soft pulse and transition effects.
const sr=48000,n=120*sr,pcm=Buffer.alloc(n*4),chords=[[220,261.626,329.628],[174.614,220,261.626],[130.813,164.814,195.998],[195.998,246.942,293.665]];
let noise=177;for(let k=0;k<n;k++){const t=k/sr,beat=t*1.6,phase=beat%1,chord=chords[Math.floor(t/10)%4];let v=0;
 for(const f of chord)v+=.022*Math.sin(2*Math.PI*f*t)*(1+.25*Math.sin(t*.5))+.011*Math.sin(2*Math.PI*f*.5*t);
 const note=chord[Math.floor(beat*2)%3]*2;v+=.06*Math.sin(2*Math.PI*note*t)*Math.exp(-7*((beat*2)%1));
 v+=.07*Math.sin(2*Math.PI*(48*phase+.04*(1-Math.exp(-45*phase))))*Math.exp(-15*phase);
 noise=(noise*1664525+1013904223)>>>0;const rand=noise/4294967296*2-1;
 for(const s of scenes){const dt=t-s.start;if(dt>-.4&&dt<.5)v+=rand*.06*Math.exp(-dt*dt/.035);if(dt>0&&dt<.5)v+=.07*Math.sin(2*Math.PI*880*dt)*Math.exp(-10*dt);}
 for(const cue of [39.5,42,51,61.5,100,104]){const dt=t-cue;if(dt>0&&dt<.08)v+=.045*Math.sin(2*Math.PI*1200*dt)*Math.exp(-70*dt);}
 if(t>49&&t<53)v+=.013*Math.sin(2*Math.PI*(600*t+70*Math.sin(t*2)))*Math.sin((t-49)*Math.PI/4)**2;
 const fade=Math.min(1,t/3,(120-t)/3);v*=fade;const left=Math.max(-1,Math.min(1,v)),right=left*(.96+.04*Math.sin(t*.7));pcm.writeInt16LE(Math.round(left*32767),k*4);pcm.writeInt16LE(Math.round(right*32767),k*4+2);
}
const header=Buffer.alloc(44);header.write('RIFF');header.writeUInt32LE(36+pcm.length,4);header.write('WAVEfmt ',8);header.writeUInt32LE(16,16);header.writeUInt16LE(1,20);header.writeUInt16LE(2,22);header.writeUInt32LE(sr,24);header.writeUInt32LE(sr*4,28);header.writeUInt16LE(4,32);header.writeUInt16LE(16,34);header.write('data',36);header.writeUInt32LE(pcm.length,40);fs.writeFileSync('public/original-score.wav',Buffer.concat([header,pcm]));
run(['-i','voiceover.wav','-i','public/original-score.wav','-filter_complex','[1:a]volume=0.22[m];[0:a][m]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]','-map','[a]','-t','120','-ar','48000','-ac','2','public/soundtrack.wav']);
for(const s of scenes.filter(s=>s.clip)){
 const input=`public/raw/${s.clip}.webm`,d=duration(input),ratio=(s.duration-.4)/d;
 run(['-i',input,'-an','-vf',`setpts=${ratio}*PTS,fps=30,tpad=stop_mode=clone:stop_duration=1`,'-t',String(s.duration),'-c:v','libx264','-preset','fast','-g','1','-bf','0','-crf','17','-pix_fmt','yuv420p',`public/clips/${s.clip}.mp4`]);
}
const stamp=s=>{const ms=Math.round(s*1000);return `${String(Math.floor(ms/3600000)).padStart(2,'0')}:${String(Math.floor(ms/60000)%60).padStart(2,'0')}:${String(Math.floor(ms/1000)%60).padStart(2,'0')},${String(ms%1000).padStart(3,'0')}`;};
fs.writeFileSync('subtitles.srt',captions.map((c,i)=>`${i+1}\n${stamp(c.start)} --> ${stamp(c.end)}\n${c.text}\n`).join('\n'));
fs.writeFileSync('narration_script.txt',script);fs.writeFileSync('src/timeline.json',JSON.stringify({scenes,captions},null,2));
console.log('Prepared timed narration, original score, captions and six real browser clips.');
