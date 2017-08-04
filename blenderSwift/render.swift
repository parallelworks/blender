import "stdlib.v2";

type file;

############################################
# ------ INPUT / OUTPUT DEFINITIONS -------#
############################################

# - Input
# The trajectory of the camera along the streamlines will have 2^N-1 points
int N   = 6;
# The trajectory of the camera around the domain will have Nloop points
int Nloop = 80;

file grassFile     <strcat("inputs/grass.jpg")>;
file x3dFiles[]    <filesys_mapper;location="x3dFiles">;
file sceneOptions  <strcat("inputs/sceneOptions.txt")>;
file utils[]       <filesys_mapper;location="utils">;
file renderframes[] <simple_mapper; prefix="outputs/frames_", suffix=".png">;

# Output
file animation   <"outputs/animation.gif">;
file camPath       <strcat("outputs/camPath.npy")>;

##############################
# ---- APP DEFINITIONS ----- #
##############################

# Calculates the path along the streamlines using fractal interpolation and smoothing.
# Must choose high enough N or else adjust the smoothing.
# 
app (file camPath) camPathCalc (file sceneOptions, file[] utils, file[] x3dFiles, int N) {
        #bash "utils/camPathCalc.sh" filename(sceneOptions) filename(camPath);
        blender "-b" "--python" "utils/camPathCalc.py" filename(sceneOptions) filename(camPath) N;

}
# Will render the scene according to sceneOptions.txt. However, the camera focus and location has been hacked so that it
# is always inputed manually (that is why there is only 1 sceneOptions.txt file even though there are 2 different camera
# behaviors. The camera location and focus are specified for each scene from the camPath file. The camera looks from its current
# location towards its next location. 
app (file out) render (file sceneOptions, int sceneNumber, file camPath, file[] utils, file[] x3dFiles, file grassFile) {
        blender "-b" "--python" "utils/renderScene.py" filename(sceneOptions) filename(out) sceneNumber filename(camPath);
        #blender -b --python 'utils/renderScene.py' 'inputs/sceneOptions.txt' 'blendedFiles/test0001' 1 'outputs/camPath.npy'
}

# In this case, the camera position has been hacked such that is loops around the domain at some angle that depends on the scene number.
# The camera should start and end at the same spot. This spot corresponds to the begining of the streamline trayectory.

app (file out) renderLoop (file sceneOptions, int sceneNumber, int Nloop, file camPath, file[] utils, file[] x3dFiles, file grassFile) {
        blender "-b" "--python" "utils/renderLoop.py" filename(sceneOptions) filename(out) sceneNumber Nloop filename(camPath);
       #blender "-b" "--python" "utils/renderLoop.py" "inputs/sceneOptions.txt" "blendedFiles2/test" 0 4 "outputs/camPath.npy"

}

# Generates a gif animation with all the scenes.
app (file o) convert (file s[])
{
  convert "-delay" 8 "-loop" 0 "outputs/frame**" filename(o);
}

######################
# ---- WORKFLOW ---- #
######################
# - Calculate camera trajectory
camPath=camPathCalc(sceneOptions,utils,x3dFiles,N);

# - Render a scene for each camera position
# Total number of scenes
int Nsim=toInt(pow(toFloat(2),toFloat(N))-1)+Nloop;
# Render loop around the domain
foreach scene in [0:Nloop]{
    renderframes[scene]=renderLoop(sceneOptions,scene,Nloop,camPath,utils,x3dFiles,grassFile);
}
# Render trajectory along the streamlines
foreach scene in [Nloop+1:Nsim]{
    renderframes[scene]=render(sceneOptions,scene-Nloop,camPath,utils,x3dFiles,grassFile);
} 
# Create animation with all scenes
animation=convert(renderframes);