#########################
## Blender bpy script  ##
######################### 

This folder contains two ready-to-go examples of a blender script for rendering .x3d files.
One example correponds to the damBreak tutorial in OpenFOAM and the other to elbow case.

# SCRIPTS
The folder contains 2 scripts: 

1. renderScene.py: Will render a scene as specified in sceneOptions.txt by running the command:
   blender -b --python renderScene.py 'sceneOptions.txt'
2. genAnimation.sh: Will sweep throgh various scenes to generate an animation by running the command:
   ./genAnimation.sh
   The script creates sceneOptions.txt from paramSceneOptions_elbow.txt or paramSceneOptions_damBreak.txt
   depending on which case you want to run. 

Both scripts are heavily commented if more details are needed.

#INPUT
Therefore, the input comes from the json file sceneOptions.txt which is structured by lines:

- Line 1: Contains the general scene information:
The user must always specify the following
1. horizonColor: background color of the scene
2. path2blended: path/name of the output
3. orientation: Determines the layout of the scene. That is, the camera location and the point it 
   will be looking at. Choose one option from group 3.1 OR 3.2 below.
   3.1 iso, front, back, left, right, up, down. If an option this group is selected:
        the user MUST specify the following field:
        3.1.1 focus: mesh object (.x3d iso volume) that the camera will be looking at. The meshes
              are numbered according to the order in which they are imported (see Lines>1) such that
              Mesh1 is the name of the first imported object (defined in Line=2) and so on.
        the user CAN specify the following field: 
        3.1.2 distance: If its value is different from zero it will be used as the distance between the
              camera and the focus. Otherwise, a default value will be selected
   3.2 none: If this option is selected, the user needs to specify the following fields
        3.2.1 camLocation: Location of the camera
        3.2.2 focusPoint: Point that the camera will be looking at

- Lines>1: Each line refers to an imported mesh object and contains the following information about it
1. path2mesh: path/name to input .x3d object
2. material: material of the mesh. Choose one option from groups 2.1, 2.2 OR 2.3 below
   2.1 water, glass: Material will look like water or glass
   2.2 none: Material will look as in paraview
   2.3 color: The user may specify the color of the material by filling in the fields
       2.3.1: diffuse
       2.3.2: specular
       2.3.3: alpha
