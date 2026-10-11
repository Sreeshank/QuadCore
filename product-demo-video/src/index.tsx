import React from 'react';
import {registerRoot,Composition} from 'remotion';
import {Demo} from './video';
const Root=()=> <Composition id="TaxReadyCinematic" component={Demo} durationInFrames={3600} fps={30} width={1920} height={1080}/>;
registerRoot(Root);
