#!/bin/bash

Nscenes=19
for scene in `seq 0 $Nscenes`
do
  echo $scene
  sed "s/@num@/$scene/g" sceneOptions.txt > sceneOptions2.txt
  blender -b --python renderScene.py 'sceneOptions2.txt'>log
done
