#########################
## Blender bpy script  ##
######################### 

This folder contains 3 ready-to-go examples of a blender script for rendering .x3d files.
One example correponds to the damBreak tutorial in OpenFOAM and the other 2 to elbow 2D and 3D cases.

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
The scene consists of the following objects: ground plane, light plane, camera and imported meshes.
The input to define this objects comes from the json file sceneOptions.txt which is structured by lines:

- Line 1: Contains the general scene information:

The user must always specify the following

1. horizonColor: background color of the scene
2. groundSize: Size of each of the 4 edges of the ground plane. Value zero triggers default option.
3. groundMaterial: Material of the ground. The user may choose any material from the material list at the end
                   of this document.
   3.1 groundColor: If groundMaterial="color" then you must also specify the rgb color.
4. lightSize: Same as groundSize but for the light plane.
5. lightIntensity: A large lightSize with low lightIntensity produces homogeneous lighting and no shadows.
                   On the other hand, a small lightSize with high lightIntensity produces shadows.
6. lightColor: The color of the lightPlane

- Lines 2 and 3: Define the position and orientation of the camera and light plane, respectively.
Their position is defined by the attribute "location". Their orientation is such that they look from their
location towards their focus, specified in the attribute "focus". The user may specify this two values directly
for which "option": "none" must be selected. Otherwise, the user may select a predefined configuration and these
two attributes will be calculated automatically.

1. location: Position of the camera or the light plane
2. focus: The camera or lightPlane will look from their location towards their focus
3. option: The user may specify attributes 1 and 2 directly and type "option": "none". However, several options are
           available to automatically calculate these atributes. User may select: front, back, up, down, left, right,
           iso1, iso2, iso3 or iso4. The iso refers to isometric view and the number to the quadrant in which the 
           camera or lightPlane will be located.
4. focusObject: The options in attribute 3 refer to the location of the focusObject which must be specified by the user
                by typing "focusObject": "Mesh#" where # is the mesh number. The meshes are numbered according to the 
                order in which they are imported (see Lines>3)such that Mesh1 is the name of the first imported object (
                defined in Line=4) and so on. If mesh1 is selected as focusObject the camera or lightPlane will be located
                and orientated as specified in "option" with respect to mesh1.
5. distance: Note that the attribute "option" only refers to the orientation and not to the distance from the camera or lightPlane
             to the focusObject. Therefore, the user can specify the distance between these objects or type 0 to trigger the default
             option.

- Lines>3
The following lines define each of the individual imported objects or meshes. This objects will be imported according to the order in
the sceneOptions.txt file (or paramSceneOptions_case.txt) such that the first object to be imported is defined in line 4 and assigned 
the name Mesh1.

1. path2mesh: Path to the .x3d mesh
2. material: Choose the material of the mesh from the list of materials at the end of this document
  2.1 color: if "color" or "light" are chosen as the material the user must specify the desired rgb color of these
  2.2 lightIntensity: if light is chosen as the material the user must specify the light intensity.

3. orientation: Determines the layout of the scene. That is, the camera location and the point it 
   will be looking at. Choose one option from group 3.1 OR 3.2 below.
   3.1 iso, front, back, left, right, up, down. If an option this group is selected:
        the user MUST specify the following field:
        3.1.1 focus: mesh object (.x3d iso volume) that the camera will be looking at. The meshes
              are numbered according to the order in which they are imported (see Lines>1) such that
              Mesh1 is the name of the first imported object (defined in Line=2) and so on.
        the user CAN specify the following field: 


# OUTPUT: In the examples, the path to the output is specified in variable path2blended of the .sh
          scrips.

# LIST OF MATERIALS: glass, water, mirror, color and light.
