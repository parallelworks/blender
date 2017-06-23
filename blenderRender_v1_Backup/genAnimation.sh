#!/bin/bash

# Number of scenes to be rendered
Nscenes=20 #9
# Name of the stout file for debugging
logFileName='blenderLog.txt'
# Chose case: damBreak or elbow
rm 'sceneOptions.txt'
options='paramSceneOptions_damBreak.txt' #'paramSceneOptions_elbow.txt'
echo 'Starting Animation ...' >$logFileName
for scene in `seq 1 $Nscenes`
do
  echo "Scene: $scene/$Nscenes"
  # Changing path/name of the input/output files 
  sed "s/@num@/$scene/g" $options > sceneOptions.txt
  echo "Scene: $scene">>$logFileName
  echo 'Starting ...'>>$logFileName
  blender -b --python renderScene.py 'sceneOptions.txt'>>$logFileName
  echo 'Completed ...'>>$logFileName
  echo '----------------------'>>$logFileName
done
# Generating .gif anumation
# WARNING: scenes for animation are not properly organized!!!
#convert $(for a in blendedFiles/elbow/**.png; do printf -- "-delay 10 %s " $a; done; ) animation.gif
convert $(for a in blendedFiles/damBreak/**.png; do printf -- "-delay 10 %s " $a; done; ) animation.gif
