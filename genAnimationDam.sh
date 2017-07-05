#!/bin/bash

# Number of scenes to be rendered
Nscenes=20
# Name of the stout file for debugging
logFileName='blenderLog.txt'
# Chose case: damBreak or elbow
rm 'sceneOptions.txt'
#options='paramSceneOptions_damBreak.txt'
options='paramSceneOptions_damBreak.txt'

echo 'Starting Animation ...' >$logFileName
for scene in `seq 1 $Nscenes`
do
  sceneName=`printf %04d%s ${scene%}`
  path2blended="blendedFiles/damBreak/$sceneName"
  echo "Scene: $scene/$Nscenes"
  # Changing path/name of the input/output files 
  sed "s/@num@/$scene/g" $options > sceneOptions.txt
  echo "Scene: $scene">>$logFileName
  echo 'Starting ...'>>$logFileName
  blender -b --python renderScene.py 'sceneOptions.txt' $path2blended>>$logFileName
  echo 'Completed ...'>>$logFileName
  echo '----------------------'>>$logFileName
done
# Generating .gif animation
convert $(for a in blendedFiles/damBreak/**.png; do printf -- "-delay 10 %s " $a; done; ) blendedFiles/damBreak/animation.gif
