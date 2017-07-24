##########################
### renderPathLines.py ###
##########################

renderPathLines.py will calculate and render the pathlines of the flow. The code locates cones at random locations
within the fluid domain. The cones are pointing in the direction of the local velocity and can be colored to indicate
the maxixmum of the local Umag, Ux, Uy, Uz or P. The position and velocities of the cones is updated at every time-step
and blue pathlines are drawn marking the previous positions of the cones.

This script is build upon the renderScene.py code. Therefore, it includes all the previous features and inputs. The
purpose of this document is to describe the new features and inputs. Several scene options can be chosen by the user
in file sceneOptions.txt. Remember that lines 1, 2 and 3 correspond to general scene options, camera options and
light options, respectively. Now, line 4 has been included to define the pathlines options. Finally, lines >4 contain
the rendering options for each of the imported meshes, as described in the renderScene.py documentation.

# Example run:
First, run the following command:
blender -b --python renderPathLines.py sceneOptions.txt blended
The sceneOptions are read from the sceneOptions.txt file and the output .png files with the scenes are saved under
the blended directory.
Then you can create an animation by running the command:
./createGif.sh blended
where blended is the path to the .png files.

# sceneOptions.txt #

Line 2 --> new attribute: 
angVel: is used to calculate the angular velocity of the camera. Specifically, this parameter corresponds to the number 
        of scenes required for the camera to loop 360 degrees round its focus object. If angVel=0 the camera will remain 
        in the specified position, as described in the renderScene.py documentation.

Line 4 --> Pathline options
startTime: Starting time for the pathlines. Must be chosen after the first saved fields in OpenFOAM.
endTime: Ending time for the pathlines. If this time is larger than the the time at which the latest OpenFOAM field was saved
         the last svaed fields will be used as the steady state solution.
dt: Time-step for calculating the pathlines and rendering the scenes. For starTime=1, endTime=2.5 and dt=0.5 four scenes would
    be created and saved corresponding to instants 1, 1.5, 2 and 2.5. 
path2case: path to the OpenFOAM case
nD: Number of dimensions of the OpenFOAM problem. Must be 2 (2D) or 3 (3D).
colorScale: Choose Umag, Ux, Uy, Uz or P for grading the color of the cones according to the local magnitud of the velocity,
            its streamwise, vertical and spanwise components or the pressure, respectively. The maximum (red) and minimum (blue)
            are calculated taking into account all the time-steps.
coneNumber: Number of randomly distributed cones. The cones are randombly distributed through the cells. Therefore, more cones
            will be present near finer mesh regions.
coneHeight: Height of the cones in blender units
coneRadius: Radios of the cones in blender units
