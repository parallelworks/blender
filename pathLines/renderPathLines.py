import numpy as np
import bpy
import math
import sys
import json
import random

from os import listdir
from subprocess import call
from scipy.interpolate import griddata

# This class deals with several aspects of OpenFoam fields
class OpenFoamFields():
     def __init__(self):
       # Starting and ending times in the controlDict file
       self.startTime=0
       self.endTime=0
       # Time interval in time units between saved fields
       self.writeInt=0
       # Path to the OpenFOAM case
       self.path2case='def'
       # List with all the saved fields
       self.savedTimes=[] # Time at which fields are saved in simulation time units
       self.savedPaths=[] # Name of the folder with the fields
       # Number of dimensions of the problem: 2 or 3.
       self.nD=3
       # Mesh information:
       # Not all the OpenFOAM mesh information will be imported, only the one currently required by the code.
       # faces[i]=[p1,...,pj,...,pn] stores the points pj that define face i
       self.faces=[]
       # points[pj]=[xp,yp,zp] stores the x,y and z coordinates of point pj
       self.points=[]
       # boundary[i,0] and boundary[i,1] store the number of faces "Nf" and the first face "sf"
       # such that the consecutive faces between "sf" and "sf+Nf" belong to boundary i
       self.boundary=[]

     # Uses the path to the OpenFoam case to initialize
     # the class atributes. The user must also specify
     # the number of dimensions of the problem: nD.
     def readMesh(self,path):
       # Read the faces file into self.faces
       path2faces=path+'/constant/polyMesh/'+'faces'
       ffaces=open(path2faces,'r')
       startReading=0
       f=0
       Nfaces=0
       for line in ffaces:
          if startReading==0:
            if '(' in line:
              startReading=1
              Nfaces=int(prevLine)
          elif f<Nfaces:
            line=line[line.find("(")+1:line.find(")")]
            strPoints=line.split(' ')
            intPoints=[]
            for p in strPoints:
               intPoints.append(int(p))
            self.faces.append(intPoints)
            f=f+1
          prevLine=line
       # Read the points file into self.points
       path2points=path+'/constant/polyMesh/'+'points'
       fpoints=open(path2points,'r')
       startReading=0
       p=0
       Npoints=0
       for line in fpoints:
          if startReading==0:
            if '(' in line:
              startReading=1
              Npoints=int(prevLine)
          elif p<Npoints:
              line=line[line.find("(")+1:line.find(")")]
              strCoord=line.split(' ')
              floatCoord=[]
              for c in strCoord:
                 floatCoord.append(float(c))
              self.points.append(floatCoord)
              p=p+1
          prevLine=line 
       # Read the boundary file into self.boundary
       path2boundary=path+'/constant/polyMesh/'+'boundary'
       fboundary=open(path2boundary,'r')
       startReading=0
       b=0
       Nbc=0
       for line in fboundary:
           if startReading==0:
             if '(' in line:
               startReading=1
               #print('Nbc')
               Nbc=int(prevLine)
               #print(Nbc)
               self.boundary=np.zeros((Nbc,2),dtype=np.integer)
           elif 'nFaces' in line:
               nFaces=''
               for c in line:
                 if c.isdigit() or c=='.':
                   nFaces=nFaces+c
           elif 'startFace' in line:
               startFace=''
               for c in line:
                 if c.isdigit() or c=='.':
                   startFace=startFace+c
               self.boundary[b,0]=int(nFaces)
               self.boundary[b,1]=int(startFace)
               b=b+1
           prevLine=line

     # Reads the controlDict information into self.startTime, self.endTime and self.savedTimes.
     # Reads the path2case directory to find the saved fields: 0, 1, 2 or 0, 0.1, 0.2, etc.
     def initialize(self,path2case,nD):
       self.path2case=path2case
       self.nD=nD
       path2controlDict=self.path2case+"/system/controlDict"
       fcontrolDict=open(path2controlDict,'r')
       for line in fcontrolDict:
          words=line.split(' ');
          if "startTime" in words:
             startTime=''
             for c in line:
                if c.isdigit() or c=='.':
                  startTime=startTime+c
             startTime=float(startTime)
          elif "endTime" in words:
             endTime=''
             for c in line:
                if c.isdigit() or c=='.':
                  endTime=endTime+c
             endTime=float(endTime)
          elif "deltaT" in words:
             deltaT=''
             for c in line:
                if c.isdigit() or c=='.':
                  deltaT=deltaT+c
             deltaT=float(deltaT)
          elif "writeControl" in words:
              #print(words)
              if "timeStep;\n;" in words:
                writeControl="timeStep;\n"
              elif "runTime;" in words:
                writeControl="runTime;\n"
              elif "adjustableRunTime;\n" in words:
                writeControl="runTime"
              else:
                print('Error: writeControl method is not supported.')
          elif "writeInterval" in words:
             writeInterval=''
             for c in line:
                if c.isdigit() or c=='.':
                  writeInterval=writeInterval+c
             #print(writeInterval)
             writeInterval=int(float(writeInterval))
       #print('deltaT')
       #print(deltaT)
       if writeControl=='timeStep':
          self.writeInt=writeInterval*deltaT
       elif writeControl=='runTime':
          self.writeInt=writeInterval
       #print(self.writeInt)
       self.startTime=startTime
       self.endTime=endTime
       Nfields=int((self.endTime-self.startTime)/self.writeInt)
       self.savedTimes=np.zeros(Nfields+1,dtype=np.double)
       for k in range(Nfields+1): 
           self.savedTimes[k]=self.writeInt*k
       directories=listdir(self.path2case)
       directories.sort()
       print(directories)
       k=0
       for d in directories:
          savedPath=''
          isPath=0
          for c in d:
                if c.isdigit() or c=='.':
                   savedPath=savedPath+c
                   isPath=1
                else:
                   isPath=0
                   break
          if isPath:
            #print(savedPath)
            self.savedPaths.append(savedPath)
            #print(self.savedPaths[k])
            k=k+1
  
     # Reads the instantaneous pressure and velocity fields saved under path2instant
     # into the array Fields. Note that OpenFoam stores the value of these fields in
     # the center of the cells. Therefore, the x, y and z coordinates of a any cell
     # e are stored in Fields[e,0], Fields[e,1] and Fields[e,2], respectively.
     # provide the x, y and z coordinates of the center of cell "e", respectively. 
     # Similarly, the Ux, Uy, Uz and P fields corresponding to cell "e" are stored in
     # Fields[e,3], Fields[e,4], Fields[e,5] and Fields[e,6]. 
     def getInstFields(self,path2instant):
       fccx=open(path2instant+'/ccx','r')
       Lfccx=fccx.readlines()
       fccy=open(path2instant+'/ccy','r')
       Lfccy=fccy.readlines()
       fccz=open(path2instant+'/ccz','r')
       Lfccz=fccz.readlines()
       fU=open(path2instant+'/U','r')
       LfU=fU.readlines()
       fp=open(path2instant+'/p','r')
       Lfp=fp.readlines()
       k=0
       startLine=0
       initField=0
       elem=0
       for line in LfU:
          if initField==0:
             words = line.split(' ');
             for word in words:
                if word=="internalField":
                  initField=1
                  startLine=k
          elif initField==1:
            nel=int(LfU[k])
            Fields=np.zeros((nel,7),dtype=np.double)
            initField=2
          elif initField==2 and k>startLine+2 and k<=startLine+2+nel:
            ccx=float(Lfccx[k])
            Fields[elem,0]=ccx
            ccy=float(Lfccy[k])
            Fields[elem,1]=ccy
            if self.nD==2:
               ccz=0.0
            elif self.nD==3:
               ccz=float(Lfccz[k])
            else:
               print("Wrong number of dimensions nD. Must be 2 or 3!!!")
            Fields[elem,2]=ccz
            line=line[line.find("(")+1:line.find(")")]
            velComponents=line.split(' ')
            n=3
            for velComponent in velComponents:
             Fields[elem,n]=float(velComponent)
             n=n+1
            p=float(Lfp[k])
            Fields[elem,6]=p
            elem=elem+1 
          k=k+1
       return Fields

     # Combines timeInterp with spatialInterp to provide the velocity and pressure fields at
     # any time t and point (x,y,z).
     def interpolate(self,t,x,y,z):
       # Interpolation in time:
       interpFields=self.timeInterp(t)
       # Interpolation in space
       txyz2UVWP=self.spatialInterp(x,y,x,interpFields)
       return txyz2UVWP

     # Interpolates between the saved fields to calculate their value at a given instant t.
     # If t>timespan of simulation, last saved field is extrapolated (steady state)
     # Bug:  Won't work with t between init conditions and first saved fields
     def timeInterp(self,t):
       # Interpolation in time:
       div_t=float(t)/float(self.writeInt)
       mod_t=int(div_t)
       if mod_t>0:
         if mod_t==div_t and mod_t<=self.endTime: # No interpolation is needed
           path2fields=self.path2case+"/"+self.savedPaths[mod_t]
           interpFields=self.getInstFields(path2fields)
         # If time is beyond simulation timespan the last fields will be assumed
         # as steady state.
         elif mod_t>=self.endTime: # Extrapolation to latest field
           path2fields=self.path2case+"/"+self.savedPaths[-1]
           interpFields=self.getInstFields(path2fields)
         else: # Interpolation is needed
           alpha=(t/self.writeInt)-mod_t
           # Previous fields
           path2prev=self.path2case+"/"+self.savedPaths[mod_t]
           prevFields=self.getInstFields(path2prev)
           # Next fields
           path2next=self.path2case+"/"+self.savedPaths[mod_t+1]
           nextFields=self.getInstFields(path2next)
           interpFields=(1-alpha)*prevFields+alpha*nextFields
       else:
         print('Cannot use initial conditions to interpolate. Select a later time.')
       return interpFields
     # Calculates the value of the pressure and velicity fields at a given point (x,y,z)
     # by interpolating the value of these fields at the center of the cells (Fields).
     # If (x,y,z) is outside of the domain, the value nan is returned.
     def spatialInterp(self,x,y,z,Fields):
       # Interpolation in space
       option='nearest'
       txyz2UVWP=np.zeros(4,dtype=np.double)
       if self.nD==2:
         txyz2UVWP[0:4]=griddata(Fields[:,[0,1]],Fields[:,3:7],(x,y),method=option)
       elif self.nD==3:
         txyz2UVWP[0:4]=griddata(Fields[:,[0,1,2]],Fields[:,3:7],(x,y,z),method=option)
       return txyz2UVWP
     # Provides the minimum MinAndMax[0] and maximum MinAndMax[1] of the desired field at time "t".
     # Available fields: P, Ux, Uy, Uz, Umag. 
     def  minmax(self,field,t):
       MinAndMax=np.zeros(2,dtype=np.double)
       # Interpolation in time:
       interpFields=self.timeInterp(t)
       if field=='P':
         MinAndMax[0]=np.amin(interpFields[:,6])
         MinAndMax[1]=np.amax(interpFields[:,6])
       elif field=='Ux':
         MinAndMax[0]=np.amin(interpFields[:,3])
         MinAndMax[1]=np.amax(interpFields[:,3])
       elif field=='Uy':
         MinAndMax[0]=np.amin(interpFields[:,4])
         MinAndMax[1]=np.amax(interpFields[:,4])
       elif field=='Uz':
         MinAndMax[0]=np.amin(interpFields[:,5])
         MinAndMax[1]=np.amax(interpFields[:,5])
       elif field=='Umag':
         nel=np.size(interpFields,0)
         Umag=np.zeros(nel,dtype=np.double)
         for e in range(nel):
            Umag[e]=np.sqrt(np.power(interpFields[e,3],2)+np.power(interpFields[e,4],2)+np.power(interpFields[e,5],2))
         MinAndMax[0]=np.amin(Umag)
         MinAndMax[1]=np.amax(Umag)
       else:
         print(("There is no field named: %s. Choose: Umag, Ux, Uy, Uz or P") % field)
       return MinAndMax
     # Provides the minimum MinAndMax[0] and maximum MinAndMax[1] of the desired field throught the timespan of the simulation.
     # Available fields: P, Ux, Uy, Uz and Umag.
     def allTimeMinmax(self,field):
        k=0
        print(self.savedPaths)
        for savedFields in self.savedPaths:
           print(savedFields)
           if k==1:
             MinAndMax=self.minmax(field,savedFields)
           elif k>1:
             MinAndMax_new=self.minmax(field,savedFields)
             if MinAndMax_new[0]<MinAndMax[0]:
               MinAndMax[0]=MinAndMax_new[0]
             if MinAndMax_new[1]>MinAndMax[1]:
               MinAndMax[1]=MinAndMax_new[1]
           k=k+1
        return MinAndMax

# Defines the relative position between an object's location and its focus point
class relativePosition():
  def __init__(self):
    # If options='none' specify:
     self.focus=(0,0,0)
     self.location=(0,0,0)
    # Else:
     # Camera options:
     # iso1, iso2, iso3, iso4, front, back, top, bottom, left, right, none
     self.option='none'
     # Relative distance distance
     # Zero value will trigger the default option
     self.distance=0
     # Object will look towards the focus object (imported volume)
     self.focusObject='def'
     # The camera will loop 360 degrees around the focus object every self.angVel scenes
     self.angVel=0
  # Moves the object to the (x,y,z) location calculated from relativePosition.self
  def setLocation(self,ob):
     if self.option!='none':
        focusOb=bpy.data.objects[lightPos.focusObject]
        objectSize=focusOb.dimensions
        objectLocation=focusOb.location
        p1=-(objectLocation[0]+objectSize[0])/2
        p2=(objectLocation[1]+objectSize[1])/2
        p3=(objectLocation[2]+objectSize[2])/2
        self.focus=(p1,p2,p3)
        # Determining distance option
        if self.distance==0:
           self.distance=3*max(objectLocation[0]+objectSize[0],objectLocation[1]+objectSize[1],objectLocation[2]+objectSize[2])
        # Determining location option
        if self.option=='iso1':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,self.distance*cos45,self.distance*cos45)
        elif self.option=='iso2':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,-self.distance*cos45,self.distance*cos45)
        elif self.option=='iso3':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,-self.distance*cos45,-self.distance*cos45)
        elif self.option=='iso4':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,self.distance*cos45,-self.distance*cos45)
        elif self.option=='front':
           self.location=(p1,p2,self.distance)
        elif self.option=='back':
           self.location=(p1,p2,-self.distance)
        elif self.option=='right':
           self.location=(p1,self.distance,p3)
        elif self.option=='left':
           self.location=(p1,-self.distance,p3)
        elif self.option=='up':
           self.location=(-self.distance,p2,p3)
        elif self.option=='down':
           self.location=(self.distance,p2,p3)
     else: # User defined focusPoint and camLocation --> calc distance
        r=0
        for i in range(3):
           aux=self.focus[i]-self.location[i]
           r=r+aux*aux
        self.distance=math.sqrt(r)
     ob.location=self.location
     return ob
  # Orientates the object such that that it looks from the self.location to self.focus
  # The angles are defined using the aircraft convention where the (y,z) plane is the 
  # ground and x is the vertical axis
  def setOrientation(self,ob):
     roll=math.pi/2 # Always parallel to the ground
     rr=0
     for i in range(2):
         aux=self.focus[i+1]-self.location[i+1]
         rr=rr+aux*aux
     # Distance in the (y,z) plane from the self.focus to self.location
     radius=math.sqrt(rr)
     x=self.location[2]-self.focus[2]
     y=self.location[1]-self.focus[1]
     z=self.location[0]-self.focus[0]
     yaw=math.atan2(y,x)
     # Distance to the (y,z) plane along the x axis
     height=z
     pitch=math.atan2(height,radius)
     ob.rotation_euler=(pitch,yaw,roll)
     return ob
        

def assignMaterial(ob,matOption,color,lightIntensity):
    if matOption=="glass":
       ob=assignGlassMaterial(ob)
    elif matOption=="water":
       ob=assignWaterMaterial(ob)
    elif matOptions=="mirror":
       ob=assignMirrorMaterial(ob)
    elif matOption=="color":
       ob=assignColorMaterial(ob,color)
    elif matOption=="light":
       ob=assignColorMaterial(ob,color,lightIntensity)
    return ob



def assignColorMaterial(ob,color):
    mat = bpy.data.materials.new('colorMat')
    mat.diffuse_color = color
    setMaterial(ob,mat)
    return ob

# MAKE NODE-BASED MATERIAL FOR CYCLES_RENDER
def assignGlassMaterial(glassObject):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=glassObject 
    mat=bpy.data.materials.new(name="Glass")
    setMaterial(glassObject,mat)
    cmat=glassObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    # Remove nodes (clean it)
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    # Add the guy to the node view
    # Output node
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    # Toon
    #node_Toon = TreeNodes.nodes.new(type='ShaderNodeBsdfTransparent')
    node_Toon = TreeNodes.nodes.new(type='ShaderNodeBsdfGlass')
    node_Toon.location = 0,0
    # Activate to select color
    #node_Toon.inputs[0].default_value = (0.488,0.66,0.58,1)  # green RGBA
    node_Toon.inputs[1].default_value = 0.00  
    node_Toon.inputs[2].default_value = 0.00 
    # Connect the guys
    links.new(node_Toon.outputs[0], node_out.inputs[0])
    return glassObject

def assignMirrorMaterial(mirrorObject):
    matName = 'planeGlass'
    bpy.data.materials.new(matName)
    bpy.data.materials[matName].use_nodes = True
    bpy.data.materials[matName].node_tree.nodes.new(type='ShaderNodeBsdfGlass')
    inp = bpy.data.materials[matName].node_tree.nodes['Material Output'].inputs['Surface']
    outp = bpy.data.materials[matName].node_tree.nodes['Glass BSDF'].outputs['BSDF']
    bpy.data.materials[matName].node_tree.links.new(inp,outp)
    mirrorObject.active_material = bpy.data.materials[matName]
    #mirrorObject=assignGlassMaterial(mirrorObject)
    return mirrorObject

# Manualy calculates the rgb color scale for scalars between 0 (blue) and 1 (red)
def rampRGB(fac):
    if fac<=0.25:
       r=0
       g=fac*4
       b=1
    elif fac<=0.5:
       r=0
       g=1
       b=1-(fac-0.25)*4
    elif fac<=0.75:
       r=(fac-0.5)*4
       g=1
       b=0
    else:
       r=1
       g=1-(fac-0.75)*4
       b=0
    rgb=(r,g,b)
    return rgb


def assignWaterMaterial(waterObject):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=waterObject
    mat = bpy.data.materials.new(name="Water")
    setMaterial(waterObject,mat)
    cmat=waterObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    node_glass = TreeNodes.nodes.new(type='ShaderNodeBsdfGlass')
    node_glass.location =0,180
    node_glass.distribution = 'GGX'
    node_glass.inputs['Color'].default_value= (0.619,0.727,0.8,1)
    node_glass.inputs['Roughness'].default_value=0.34
    node_glass.inputs['IOR'].default_value=1.333
    links.new(node_glass.outputs[0], node_out.inputs[0])
    return waterObject

def assignLightMaterial(lightObject,color,intensity):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=lightObject
    mat = bpy.data.materials.new(name="Light")
    setMaterial(lightObject,mat)
    cmat=lightObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    node_light = TreeNodes.nodes.new(type='ShaderNodeEmission')
    node_light.location =0,0
    # First 3 values select color. Last one not sure.
    node_light.inputs[0].default_value= color #(1,1,1,0)
    node_light.inputs[1].default_value=intensity #
    links.new(node_light.outputs[0],node_out.inputs[0])
    return lightObject



def setMaterial(ob, mat):
    me = ob.data
    if len(me.materials):
       ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    return ob 


## Keeps track and renames or eliminates the imported objects according to their type and 
# the order in wich they are imported.
# Note 1: When a mesh is imported into blender it comes with default lamps and camera
# Note 2: In the current version of the code imported cameras and lamps are deleted
class objectList():
  def __init__(self):
    self.N_Object=0 # Total number of objects
    self.N_Camera=0 # Total number of cameras (Should remain =0 in current version)
    self.N_Lamp=0  # Total number of lamps (Should reamin =0 in current version)
    self.N_Mesh=0 # Total number of meshes
  # Renames the objects according to their type and the order in which they are imported
  # such that their name is Type.order
  def rename(self,item):
    self.N_Object=self.N_Object+1
    print(("Object %s") % self.N_Object)
    print(("Type: %s") % item.type)
    if item.type=='MESH':
      self.N_Mesh=self.N_Mesh+1
      oldDefName=item.name
      print(("Previous default name: %s") % item.name)
      newDefName="Mesh%s" % self.N_Mesh
      bpy.data.objects[oldDefName].name = newDefName
      print(("Current default name: %s") % item.name)
    elif item.type=='CAMERA':
      bpy.data.objects[item.name].select = True
      print(("Deleted: %s") % item.name)
      bpy.ops.object.delete() # Deletes cameras
      self.N_Object=self.N_Object-1
    elif item.type=='LAMP':
      bpy.data.objects[item.name].select = True
      print(("Deleted: %s") % item.name)
      bpy.ops.object.delete() # Deletes lamps
      self.N_Object=self.N_Object-1
    else:
      print(("WARNING - Unrecognized item type: %s") % item.name)
      print('\n')
    return item
class pathlinesOptions():
  def __init__(self):
     self.startTime=0.0
     self.endTime=0.0
     self.dt=0.0
     self.path2case='def'
     self.colorScale='Umag'
     self.coneNumber=100
     self.coneRadius=1
     self.coneHeight=3
     self.colorScale='Umag'
     self.nD=3
  def biasedSample(self,elements,sampleSize,field,biasFieldOp):
     sample4bias=random.sample(elements,sampleSize)
     sampleValues=np.zeros(sampleSize,dtype=np.double)
     for be in range(sampleSize):
       if field=='P':
         sampleValues[be]=interpFields[sample4bias[be],6]
       elif field=='Ux':
         sampleValues[be]=interpFields[sample4bias[be],3]
       elif field=='Uy':
         sampleValues[be]=interpFields[sample4bias[be],4]
       elif field=='Uz':
         sampleValues[be]=interpFields[sample4bias[be],5]
       elif field=='Umag':
         sampleValues[be]=np.sqrt(np.power(interpFields[sample4bias[be],3],2)+np.power(interpFields[sample4bias[be],4],2)+np.power(interpFields[sample4bias[be],5],2))
     sampleValues=list(sampleValues)
     if biasFieldOp=='max':
       index=sampleValues.index(max(sampleValues))
     elif biasFieldOp=='min':
       index=sampleValues.index(min(sampleValues))
     newSample=sample4bias[index]
     return newSample

# Defines the path to the .x3d files and the assigned material
class mesh():
  def __init__(self):
     self.path2mesh='def'
     self.material='def'
     self.color=(0,0,0)
class sceneOptions():
  def __init__(self):
     # Ground options
     self.groundSize=0
     self.groundMaterial='def'
     self.groundColor=(0.8,0.8,0.8)
     # Light options
     # First 3 numbers define color. Not sure what the last number does.
     self.lightSize=0
     self.lightColor=(1,1,1,1)
     self.lightIntensity=25
     # Horizon options
     self.horizonColor=(0.8,0.8,0.8)

def createLine(lineName,pointList,thickness):
    # setup basic line data
    theLineData = bpy.data.curves.new(name=lineName,type='CURVE')
    theLineData.dimensions = '3D'
    theLineData.fill_mode = 'FULL'
    theLineData.bevel_depth = thickness
    # define points that make the line
    polyline = theLineData.splines.new('POLY')
    polyline.points.add(len(pointList)-1)
    for idx in range(len(pointList)):
        polyline.points[idx].co = (pointList[idx])+(1.0,)
    # create an object that uses the linedata
    theLine = bpy.data.objects.new(lineName,theLineData)
    bpy.context.scene.objects.link(theLine)
    theLine.location = (0.0,0.0,0.0)
    # setup a material
    lmat = bpy.data.materials.new('Linematerial')
    lmat.diffuse_color = (0.0,0.0,1.0)
    lmat.use_shadeless = True
    theLine.data.materials.append(lmat)


##############################
## Starting blender script ###
##############################

bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.context.scene.render.engine = 'CYCLES'

# File containing the json formated input
so=open(sys.argv[4],'r') #so=open('sceneOptions.txt','r')
# Path for the output file
path2blended=sys.argv[5] # blended

# Deleting all objects
# Note 1: Sometimes blender is initialized with default objects: cube, light and camera
print('Deleting the following default objects:')
for item in bpy.data.objects:
    print(item.type)
    bpy.data.objects[item.name].select = True
    bpy.ops.object.delete()

sceneOp=sceneOptions()
# Reading input from json file
k=0 # Line number in the json file
OL=objectList() # Keeps track of the imported objects and their names
cmesh=mesh() # Stores the properties of the current mesh object
camPos=relativePosition() # Initialize the relative position of the camera
lightPos=relativePosition() # Initialize the relative position of the light plane
plo=pathlinesOptions()
# - Each line in the json file defines a different aspect of the scene
# Line 1: General options
# Line 2: Camera position
# Line 3: Light position
# Lines >3: Options for each imported .x3d mesh object
for line in so:
    if k==0: # Read general options
       sceneOp.__dict__= json.loads(line)
       # Defining the background color
       w=bpy.data.worlds['World']
       w.horizon_color=sceneOp.horizonColor
    elif k==1:
       camPos.__dict__=json.loads(line)
    elif k==2:
       lightPos.__dict__=json.loads(line)
    elif k==3:
       plo.__dict__=json.loads(line)
    else: # Read mesh options
       cmesh.__dict__= json.loads(line)
       ############################################################
       # Loading mesh objects and assigning default names to them #
       ############################################################
       file=cmesh.path2mesh
       print('Render %s' % file)
       bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')
       # Renaming imported items
       bpy.ops.object.select_all(action='TOGGLE')
       print('\n')
       print('Imported items:\n')
       # Items are renamed depending on the order in which they are imported
       # See objectList.rename for more info.
       j=1
       for item in bpy.data.objects:
          if j>OL.N_Object:
             item=OL.rename(item)
          j=j+1
       ######################################################
       # Renaming imported mesh and assigning it a material #
       ######################################################
       meshNumber=k-3
       name="Mesh%s" %meshNumber
       print(("%s ---> Material: %s") %(name,cmesh.material))
       bpy.data.objects[name].select = True
       bpy.ops.object.shade_smooth()
       ob=bpy.data.objects[name]
       if cmesh.material=="glass":    
          ob=assignGlassMaterial(ob)
       elif cmesh.material=="water":
          ob=assignWaterMaterial(ob)
       elif cmesh.material=="color":
          ob=assignColorMaterial(cmesh.diffuse,cmesh.specular,cmesh.alpha, ob)
    k=k+1      


#######################
# Adding ground plane #
#######################
# Creating new plane
bpy.ops.mesh.primitive_plane_add()
bpy.data.objects['Plane'].name="Ground"
ground=bpy.data.objects['Ground']
ground=assignColorMaterial(ground,(0.5,0.5,0.5))
# Parallel to the ground
bpy.data.objects['Ground'].rotation_euler=(0,math.pi/2,0)

######################
# Adding light plane #
######################
# Creating new plane
bpy.ops.mesh.primitive_plane_add()
bpy.data.objects['Plane'].name="Light"
lightPlane=bpy.data.objects['Light']
lightPlane=assignLightMaterial(lightPlane,sceneOp.lightColor,sceneOp.lightIntensity)
lightPlane=lightPos.setLocation(lightPlane)
lightPlane=lightPos.setOrientation(lightPlane)
lightPlane.dimensions=(sceneOp.lightSize,sceneOp.lightSize,sceneOp.lightSize)

############################
# Setting camera position  #
############################
# Creating a new camera
bpy.ops.object.camera_add(location=(0,0,0))
cam=bpy.data.objects['Camera']
rotateCam=1
cam=camPos.setLocation(cam)
cam=camPos.setOrientation(cam)
# The camera ONLY records objects located at a distance between clip_start and clip_end!!!
cam.data.clip_start=0
cam.data.clip_end=camPos.distance*2 # WARNING: readjust if objects are very large or far away from each-other

# Setting position and dimensions of the ground plane as a function of the camera distance and focus
if sceneOp.groundSize==0:
  dim=camPos.distance
  bpy.data.objects['Ground'].dimensions=(dim,dim,dim)
else:
  bpy.data.objects['Ground'].dimensions=(sceneOp.groundSize,sceneOp.groundSize,sceneOp.groundSize)
bpy.data.objects['Ground'].location=(0,camPos.focus[1],camPos.focus[2])

###################
# Rendering Scene #
###################
elbowFields=OpenFoamFields()
print(plo.path2case)
elbowFields.initialize(plo.path2case,plo.nD)

elbowFields.readMesh(plo.path2case)
Nbc=np.size(elbowFields.boundary[:,0])
print(elbowFields.boundary)
print('Nbc')
print(Nbc)

kp=0
firstBCFace=elbowFields.boundary[0,1]
lastBCFace=elbowFields.boundary[Nbc-1,0]+elbowFields.boundary[Nbc-1,1]
print('First and last faces')
print(firstBCFace)
print(lastBCFace)
for i in range(firstBCFace,lastBCFace):
     pts=elbowFields.faces[i]
     for p in pts:
       kp=kp+1
print(kp)
bcfields=np.zeros((kp,7),dtype=np.double)
kp=0
for i in range(firstBCFace,lastBCFace):
     pts=elbowFields.faces[i]
     for p in pts:
       coords=elbowFields.points[p]
       bcfields[kp,0]=coords[0]
       bcfields[kp,1]=coords[1]
       bcfields[kp,2]=coords[2]
       bcfields[kp,3]=np.nan
       bcfields[kp,4]=np.nan
       bcfields[kp,5]=np.nan
       bcfields[kp,6]=np.nan
       kp=kp+1
print(kp)


time=list(np.arange(plo.startTime,plo.endTime,plo.dt))
MinAndMax=elbowFields.allTimeMinmax(plo.colorScale)
initFields=elbowFields.timeInterp(plo.startTime)
nel=np.size(initFields,0)
cells=list(np.arange(nel))
nCones=plo.coneNumber # Number of cones
samples=random.sample(cells,nCones)
samplesValues=np.zeros((nCones,7),dtype=np.double)

lines=[]
recycleCone=0
ti=0
ang=0
R=camPos.distance
for t in time:
  if camPos.angVel>0:
    camAngVel=(2*math.pi)/camPos.angVel #2*math.pi/40
    #cam=camPos.setLocation(cam)
    ang=camAngVel*t
    camPos.location=(camPos.location[0],R*math.cos(ang),R*math.sin(ang))
    print(camPos.location)
    camPos.option='none'
    cam=camPos.setLocation(cam)
    cam=camPos.setOrientation(cam)
  si=0
  interpFields=elbowFields.timeInterp(t)
  interpFieldsBC=np.append(interpFields,bcfields,axis=0)
  for sample in samples:
     if np.isnan(samplesValues[si,3]):
       si=si+1
       continue
     print(("Time: %s, Sample= %s") %(t,sample))
     if ti==0:
       samplesValues[si,0:7]=initFields[sample,0:7]
       bpy.ops.mesh.primitive_cone_add()
       newname="Cone%s" %si
       bpy.data.objects['Cone'].name=newname
       cone=bpy.data.objects[newname]
       cone.dimensions=[plo.coneRadius,plo.coneRadius,plo.coneHeight]
       lines.append([])
       lines[si].append((-samplesValues[si,1],samplesValues[si,0],samplesValues[si,2]))
     else:
       dt=time[ti]-time[ti-1]
       xyz2uvwp=elbowFields.spatialInterp(samplesValues[si,0],samplesValues[si,1],samplesValues[si,2],interpFieldsBC)
       samplesValues[si,0:3]=samplesValues[si,0:3]+xyz2uvwp[0:3]*dt
       samplesValues[si,3:7]=xyz2uvwp[0:4]
       lines.append([])
       lines[si].append((-samplesValues[si,1],samplesValues[si,0],samplesValues[si,2]))
       lineName="Line%s" %si
       if ti==2:
         createLine(lineName,lines[si],0.15)
       elif ti>3:
         bpy.ops.object.select_all(action='DESELECT')
         bpy.data.objects[lineName].select = True
         #print(("Deleted: %s") % item.name)
         bpy.ops.object.delete() # Deletes cameras
         createLine(lineName,lines[si],0.15)

     if np.isnan(samplesValues[si,3]):
       if recycleCone==1:
         newSample=plo.biasedSample(cells,2,plo.colorScale,'max')
         print('newSample')
         print(newSample)
         samples[si]=newSample
         sample=newSample
         samplesValues[si,0:3]=interpFields[newSample,0:3]
         xyz2uvwp=elbowFields.spatialInterp(samplesValues[si,0],samplesValues[si,1],samplesValues[si,2],interpFieldsBC)
         samplesValues[si,3:7]=xyz2uvwp[0:4]
       else:
         bpy.ops.object.select_all(action='DESELECT')
         coneName="Cone%s" %si
         bpy.data.objects[coneName].select = True
         bpy.ops.object.delete() 
         si=si+1
         continue

     x=samplesValues[si,0]
     y=samplesValues[si,1]
     z=samplesValues[si,2]
     Ux=samplesValues[si,3]
     Uy=samplesValues[si,4]
     Uz=samplesValues[si,5]
     Umag=np.sqrt(np.power(Ux,2)+np.power(Uy,2)+np.power(Uz,2))
     P=samplesValues[si,6]

     newname="Cone%s" %si
     cone=bpy.data.objects[newname]
     conePos=relativePosition()
     conePos.location=(-y,x,z)
     conePos.focus=(-y+Uy,x-Ux,z-Uz)
     cone=conePos.setLocation(cone)
     cone=conePos.setOrientation(cone)
     if plo.colorScale=='P':
       fac=(P-MinAndMax[0])/(MinAndMax[1]-MinAndMax[0])
     elif plo.colorScale=='Ux':
       fac=(Ux-MinAndMax[0])/(MinAndMax[1]-MinAndMax[0])
     elif plo.colorScale=='Uy':
       fac=(Uy-MinAndMax[0])/(MinAndMax[1]-MinAndMax[0])
     elif plo.colorScale=='Uz':
       fac=(Uz-MinAndMax[0])/(MinAndMax[1]-MinAndMax[0])
     elif plo.colorScale=='Umag':
       fac=(Umag-MinAndMax[0])/(MinAndMax[1]-MinAndMax[0])
     color=rampRGB(fac)
     cone=assignColorMaterial(cone,color)
     si=si+1
  ti=ti+1
  bpy.ops.object.select_all()
  bpy.context.scene.camera = cam
  bpy.context.scene.cycles.samples = 100
  bpy.data.scenes['Scene'].render.filepath = path2blended+'/'+str(ti).zfill(4)
  bpy.ops.render.render(write_still = True)


call('./createGif.sh',shell=True)
