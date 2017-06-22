#!/bin/bash

# Number of scenes to be rendered
Nscenes=20
# Name of the stout file for debugging
logFileName='blenderLog.txt'
for scene in `seq 1 $Nscenes`
do
  echo "Scene: $scene/$Nscenes"
  # Changing path/name of the input/output files 
  sed "s/@num@/$scene/g" paramSceneOptions.txt > sceneOptions.txt
  echo "Scene: $scene">>$logFileName
  echo 'Starting ...'>>$logFileName
  blender -b --python renderScene.py 'sceneOptions.txt'>>$logFileName
  echo 'Completed ...'>>$logFileName
  echo '----------------------'>>$logFileName
done
# Generating .gif anumation
convert $(for a in blendedFiles/**.png; do printf -- "-delay 10 %s " $a; done; ) animation.gif
