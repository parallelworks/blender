import bpy
import math
import sys
import json
import random

from scipy.interpolate import griddata
import numpy as np


bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.context.scene.render.engine = 'CYCLES'

# File containing the json formated input
so=open(sys.argv[4],'r')
camPathName=sys.argv[5]
N=int(sys.argv[6])


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    """Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    Examples
    --------
    t = np.linspace(-4, 4, 500)
    y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
    ysg = savitzky_golay(y, window_size=31, order=4)
    import matplotlib.pyplot as plt
    plt.plot(t, y, label='Noisy signal')
    plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
    plt.plot(t, ysg, 'r', label='Filtered signal')
    plt.legend()
    plt.show()
    References
    ----------
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
    """
    from math import factorial
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')



def get_verts_edges(obj, use_modifiers=True, settings='PREVIEW'):
    scene = bpy.context.scene
    obj_data = obj.to_mesh(scene, use_modifiers, settings)
    #verts = [v.co for v in obj_data.vertices]
    verts = [obj.matrix_world*v.co for v in obj_data.vertices]
    # or..use a copy to avoid dereferencing due to the .remove()
    # verts = [v.co.copy() for v in obj_data.vertices]
    edges = obj_data.edge_keys
    bpy.data.meshes.remove(obj_data)
    return verts, edges

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

# Defines the path to the .x3d files and the assigned material
class mesh():
  def __init__(self):
     self.path2mesh='def'
     self.material='def'
     self.color=(0,0,0)
     self.lightIntensity=0


L=np.power(2,N)
L05=int(L/2)
orderVector=np.zeros((L,1),dtype=np.integer)
rangeVector=np.zeros((L,1),dtype=np.integer)
orderVector[0]=1
orderVector[1]=L
auxMatrix=np.zeros((L05,N),dtype=np.integer)
for i in range(L05):
   j=2*i+1
   n=0
   num=j*np.power(2,n)
   auxMatrix[i,n]=num
   while num<L:
      n=n+1
      num=j*np.power(2,n)
      if num<L:
        auxMatrix[i,n]=num

k=1
for j in range(N):
    jj=N-j-1
    for i in range(L05):
      num=auxMatrix[i,jj]
      if num>1:
        k=k+1
        orderVector[k]=num
        rangeVector[k]=np.power(2,jj)

# Deleting all objects
# Note 1: Sometimes blender is initialized with default objects: cube, light and camera
print('Deleting the following default objects:')
for item in bpy.data.objects:
    print(item.type)
    bpy.data.objects[item.name].select = True
    bpy.ops.object.delete()

# Reading input from json file
k=0 # Line number in the json file
OL=objectList() # Keeps track of the imported objects and their names
cmesh=mesh() # Stores the properties of the current mesh object
# - Each line in the json file defines a different aspect of the scene
# Line 1: General options
# Line 2: Camera position
# Line 3: Light position
# Lines >3: Options for each imported .x3d mesh object
meshNumber=3
kc=meshNumber+2
k=0
for line in so:
   if k==kc:
     cmesh.__dict__= json.loads(line)
   k=k+1
############################################################
# Loading mesh objects and assigning default names to them #
############################################################
file=cmesh.path2mesh
print('Render %s' % file)
#bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')
bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='-Y')
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
###########################
# Renaming imported mesh  #
###########################
name="Mesh%s" %1
print(("%s ---> Material: %s") %(name,cmesh.material))
bpy.data.objects[name].select = True
ob=bpy.data.objects[name]
## Obtaining vertices
verts, edges = get_verts_edges(ob)
del edges
Lv=len(verts)
verts2=np.zeros((Lv,3),dtype=np.double)
kk=0
for v in verts:
    verts2[kk,0]=v[0] #-y 
    verts2[kk,1]=v[1] #x
    verts2[kk,2]=v[2] #z
    kk=kk+1
kk=0
del verts
print('xmin')
zi=np.amin(verts2[:,2])
zf=np.amax(verts2[:,2])
xi=np.amin(verts2[:,1])
xf=np.amax(verts2[:,1])
yi=np.amin(verts2[:,0])
yf=np.amax(verts2[:,0])

camTraject=np.zeros((L+1,3),dtype=np.double)
camTraject[0,:]=griddata(verts2[:,[0,1,2]],verts2[:,[0,1,2]],(yi,xi,zi),method='nearest')
camTraject[1,:]=camTraject[0,:]
camTraject[L-1,:]=griddata(verts2[:,[0,1,2]],verts2[:,[0,1,2]],(yf,xf,zf),method='nearest')
camTraject[L,:]=camTraject[L-1,:]
camTraject[L-1,:]
print('here')
for cp in range(2,L):
    pos=orderVector[cp]
    ran=rangeVector[cp]
    left=pos-ran
    right=pos+ran
    aux1=camTraject[left,1]
    aux2=camTraject[right,1]
    if aux1==0:
      print('empty elem')
      print(left)
      ptculo1
    if aux2==0:
      print('empty elem')
      print(right)
      ptculo2

    xx=(camTraject[left,1]+camTraject[right,1])/2
    yy=(camTraject[left,0]+camTraject[right,0])/2
    zz=(camTraject[left,2]+camTraject[right,2])/2
    camTraject[pos-1,:]=griddata(verts2[:,[0,1,2]],verts2[:,[0,1,2]],(yy,xx,zz),method='nearest')
    if (pos%2)==0:
      camTraject[pos,:]=camTraject[pos-1,:]
    k=k+1     

camTraject[:,0]=savitzky_golay(camTraject[:,0], 11, 6) # window size (odd), polynomial order
camTraject[:,1]=savitzky_golay(camTraject[:,1], 11, 6) # window size, polynomial order
camTraject[:,2]=savitzky_golay(camTraject[:,2], 11, 6) # window size, polynomial order

np.save(camPathName,camTraject)

bpy.ops.object.select_all()
bpy.ops.object.select_all()
bpy.ops.object.delete()
