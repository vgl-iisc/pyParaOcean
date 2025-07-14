import numpy as np
import itertools
import netCDF4
import os

import vtk
from vtk import vtkPolyDataWriter, vtkMutableDirectedGraph, vtkPoints, vtkGraphToPolyData, vtkXMLPolyDataWriter
import time
import math
from scipy import ndimage
import multiprocessing as mp
import matplotlib.pyplot as plt
import datetime
import networkx as nx

import cc3d

fin = open('parameter.txt', 'r')
Lines = fin.readlines()

parameters = []
for line in Lines:
	line = line.strip()
	if len(line)!=0 and line[0]!='#' and line[0]!=' ' and line[0]!='\n':
		parameters.append(line.split('=')[1].strip())
		#print(parameters)

infile = str(parameters[5])

filename = str(parameters[6])

v_limit = int(parameters[0])

lt_origin = int(parameters[1])
ln_origin = int(parameters[2])

lt_clip = int(parameters[3])
ln_clip = int(parameters[4])

print(lt_clip, ln_clip)

interpolation = int(parameters[10])

d_max = int(parameters[7])

resolution = float(parameters[8].split('/')[0].strip())/float(parameters[8].split('/')[1].strip())

neighborhood = int(parameters[9])

v_name = str(parameters[11])

d_name = str(parameters[12])

nbrhd = int(neighborhood/(resolution*111))

lt_clip = round((lt_clip-lt_origin)/resolution)
ln_clip = round((ln_clip-ln_origin)/resolution)

print(lt_clip, ln_clip)

print('neighborhood : ',nbrhd)
print(v_limit)

print(datetime.datetime.now())

def euc_distance(p1,p2):
	dist = 0
	for i in range(len(p1)):
		diff = p1[i]-p2[i]
		dist += (diff**2)
	return np.sqrt(dist)

start = time.time()

cmd = "rm data.nc"
os.system(cmd)
cmd = "cp "+infile+" data.nc"
os.system(cmd)

DS = netCDF4.Dataset("data.nc", "a")

shape = DS.variables[v_name].shape

d_lst = np.copy(DS.variables[d_name][:]).astype('int32')

np.save('d_lst.npy', d_lst)

print(d_max,' d_max')

print(shape)

fn = mp.RawArray('d',shape[0]*shape[1]*shape[2]*shape[3])

fn_np = np.frombuffer(fn, dtype=np.float64).reshape(shape)

for t in range(shape[0]):
	fn_np[t] = np.copy(DS.variables[v_name][t].astype('float64'))

def foo3(d):
	d_c = d
	while(d_c <= d_lst[-1]):
		di = np.where(d_lst == d_c)[0]
		if(len(di)==1):
			break
		d_c+=1
	di = di[0]

	for t in range(shape[0]):
		k_s = np.zeros((shape[2], shape[3]))
		if d == d_lst[di]:
			k_s = np.copy(fn_np[t][di])
		else:
			v_mx = fn_np[t][di]
			v_mn = fn_np[t][di-1]
			alpha = (d_lst[di]-d) / (d_lst[di]-d_lst[di-1])
			val = ((alpha) * v_mn + (1-alpha) * v_mx)
			k_s = np.copy(val)

		#k_s[:,0:ln_clip+1]=0
		#k_s[0:lt_clip+1,:]=0
		k_s[k_s<0]=0
		#np.save('vol/vol_s'+str(t)+'_'+str(d)+'.npy', k_s)
		k_s[k_s<v_limit]=0
		k_s[k_s>0]=1
		np.save('vol/isovol_s'+str(t)+'_'+str(d)+'.npy', k_s)
	del k_s
	
print('interpolating and isovolume')

cmd = "rm -r vol"
os.system(cmd)
cmd = 'mkdir vol'
os.system(cmd)

pool = mp.Pool()
pool.map(foo3, np.arange(d_max))
pool.close()
pool.join()
del pool

print('interpolating and isovolume done')
del fn
del DS

def foo1(t): #computing boundary
	#for t in range(shape[0]):
	for d in range(d_max):
		fn_td = np.copy(np.load('vol/isovol_s'+str(t)+'_'+str(d)+'.npy', allow_pickle=True)).astype('float32')
		fronts=np.zeros((shape[2],shape[3])).astype('int32')
		avg = ndimage.uniform_filter(np.pad(fn_td,1), size=3)
		avg = avg[1:shape[2]+1,1:shape[3]+1]
		avg[avg<=(1/9)]=1
		avg[avg==1]=0
		avg[avg>0]=1
		
		bound = np.multiply(fn_td,avg).astype('int32')
		
		del avg
		
		ex_comps, n_comps = cc3d.connected_components(bound,return_N=True,connectivity = 8)
		del bound
		
		ex_comps = np.copy(ex_comps).astype('int32')
		
		east=[]
		west=[]
		
		for uid in range(1, n_comps+1):
			lt__,ln__ = np.where(ex_comps==uid)
			comp = zip(lt__,ln__)
			(lte,lne) = (shape[2],0)
			(ltw,lnw) = (shape[2],shape[3])
			for (lt,ln) in comp:
				
				if ln>lne or (ln==lne and lt<lte):
					(lte,lne) = (lt,ln)
				if ln<lnw or (ln==lnw and lt<ltw):
					(ltw,lnw) = (lt,ln)
			east.append((lte,lne))
			west.append((ltw,lnw))
			
		lst = zip(west,east)
		for (src,dst) in lst:
			(lt, ln) = src
			(ltr, lnr) = (lt-1, ln-1)
			stop = (ltr, lnr)
			fronts[lt,ln] = ex_comps[lt,ln]
			while((lt,ln)!=dst):
				if ltr>lt and lnr<=ln:
					lnr+=1
				elif lnr>ln and ltr>=lt:
					ltr-=1
				elif ltr<lt and lnr>=ln:
					lnr-=1
				elif lnr<ln and ltr<=lt:
					ltr+=1
				
				if ltr<0 or ltr>shape[2]-1 or lnr<0 or lnr>shape[3]-1:
					continue
				
				if ex_comps[ltr,lnr]==ex_comps[lt,ln]:
					fronts[ltr,lnr]=ex_comps[ltr,lnr]
					(lt,ln), (ltr,lnr) = (ltr,lnr), (lt,ln)
					stop = (ltr, lnr)
					continue
					
				if (ltr,lnr) == stop:
					input('ERROR in fronts')		
					break
							
		np.save('fronts/fronts_'+str(t)+'_'+str(d)+'.npy', fronts)
		del fronts
		del ex_comps
		
print('boundary and fronts')

st = time.time()

cmd = "rm -r fronts"
os.system(cmd)
cmd = "mkdir fronts"
os.system(cmd)

pool = mp.Pool()
pool.map(foo1, np.arange(shape[0]))
#foo1(0)
pool.close()
pool.join()
del pool

print((time.time()-st)/60)

print('boundary and fronts done')

half_mask = np.zeros((nbrhd, nbrhd)).astype(('int32'))
lt_ = np.arange(nbrhd)
for lt,ln in itertools.product(lt_,lt_):
	if ((nbrhd//2-lt)**2+(nbrhd//2-ln)**2)<=((nbrhd//2)**2):
		half_mask[lt,ln]=1

def foo(t): #clustering
	grid = np.zeros((d_max,shape[2],shape[3])).astype('int32')
	
	for d in range(d_max):
		front = np.load('fronts/fronts_'+str(t)+'_'+str(d)+'.npy',allow_pickle=True).astype('int32')
		front[front>0]=1
		grid[d] = np.copy(front)
	
	grid2 = np.pad(grid, pad_width=((0,0),(nbrhd//2,nbrhd//2),(nbrhd//2,nbrhd//2)), mode='constant', constant_values=0)	
	d__,lt__,ln__ = np.nonzero(grid2)
	#st = time.time()
	lst=zip(d__,lt__,ln__)
	for (d1,lt1,ln1) in lst:
		grid2[d1, lt1-(nbrhd//2):lt1+(nbrhd//2)+1, ln1-(nbrhd//2):ln1+(nbrhd//2)+1] += half_mask
				
	sh = grid2.shape
	grid2 = grid2[:,nbrhd//2:sh[1]-(nbrhd//2),nbrhd//2:sh[2]-(nbrhd//2)]
	grid2[grid2>0]=1
	
	grid2, n_comps = cc3d.connected_components(grid2,return_N=True,connectivity = 26)
	#print('labels done in ',(time.time()-st)/60,' at ', t)
	grid = np.multiply(grid,grid2)
	grid[:,:,0:ln_clip+1]=0
	grid[:,0:lt_clip+1,:]=0
		
	
	del grid2
	
	cluster_rep = dict()
	(d__,lt__,ln__)=np.nonzero(grid)
	lst = zip(d__,lt__,ln__)
	for (d,lt,ln) in lst:
		label = grid[d,lt,ln]
		if cluster_rep.get(label):
			cluster_rep[label][1]+=d
			cluster_rep[label][2]+=lt
			cluster_rep[label][3]+=ln
			cluster_rep[label][4]+=1
		else:
			cluster_rep[label]=[t,d,lt,ln,1]
	
	cluster_rep_new=dict()
	#to_del = []
	for label, [t1,d1,lt1,ln1,ct1] in cluster_rep.items():
		#if ct1<min_clstr:
		#	to_del.append(label)
		#else:
		cluster_rep[label] = [t1,d1/ct1,lt1/ct1,ln1/ct1,ct1,float('inf')]
		cluster_rep_new[label]= [t1,d1/ct1,lt1/ct1,ln1/ct1,ct1]

	#[cluster_rep. pop(label) for label in to_del]
	#del to_del

	for (d,lt,ln) in lst:
		label = grid[d,lt,ln]
		if cluster_rep.get(label):
			(t1,d1,lt1,ln1,ct1,dist1) = cluster_rep[label]
		else:
			continue
		dist = euc_distance((d,lt,ln),(d1,lt1,ln1))
		if dist<dist1:
			cluster_rep_new[label] = [t,d,lt,ln,ct1]
			cluster_rep[label][5]=dist
	
	np.save('vol/cluster_rep'+str(t)+'.npy', cluster_rep_new)
	
	for d in range(d_max):
		np.save('fronts/surface_fronts_'+str(t)+'_'+str(d)+'.npy', grid[d])
	return n_comps
	
print('surface_fronts')

st = time.time()

pool = mp.Pool()

n_comps = pool.map(foo, np.arange(shape[0]))
n_comps=np.copy(n_comps).astype('int')

print('surface fronts = ', np.sum(n_comps))

pool.close()
pool.join()
del pool

del half_mask
print((time.time()-st)/60)

print('surface_fronts done')
full_mask = np.zeros((2*nbrhd+1, 2*nbrhd+1)).astype(('int32'))
lt_ = np.arange(2*nbrhd+1)
for lt,ln in itertools.product(lt_,lt_):
	if ((nbrhd-lt)**2+(nbrhd-ln)**2)<=((nbrhd)**2):
		full_mask[lt,ln]=1

def foo2(t): #edges
	if t>=shape[0]-1: return
	edges = set()
	for d in range(d_max):
		fronts = np.load('fronts/surface_fronts_'+str(t)+'_'+str(d)+'.npy', allow_pickle=True).astype('int32') 
		nxt_fronts = np.load('fronts/surface_fronts_'+str(t+1)+'_'+str(d)+'.npy', allow_pickle=True).astype('int32')
		fronts = np.pad(fronts,nbrhd)
		nxt_fronts = np.pad(nxt_fronts,nbrhd)
		flag_l=False
		flag_h=False
		
		if d+1<d_max:
			nxt_fronts_h = np.load('fronts/surface_fronts_'+str(t+1)+'_'+str(d+1)+'.npy', allow_pickle=True).astype('int32')
			flag_h=True
			nxt_fronts_h = np.pad(nxt_fronts_h,nbrhd)
		
		lt_, ln_ = np.nonzero(fronts)
		lst = zip(lt_,ln_)
		for lt,ln in lst:
			temp = np.multiply(nxt_fronts[lt-nbrhd:lt+nbrhd+1,ln-nbrhd:ln+nbrhd+1],full_mask)
			dst_lst = np.unique(temp)
			if flag_h:
				temp = np.multiply(nxt_fronts_h[lt-nbrhd:lt+nbrhd+1,ln-nbrhd:ln+nbrhd+1],full_mask)
				temp = np.unique(temp)
				dst_lst = np.concatenate((dst_lst,temp))
				dst_lst = np.unique(dst_lst)				
			for uid in dst_lst:
				e = ((t,fronts[lt,ln]), (t+1,uid))
				edges.add(e)
	
	edges = np.copy(list(edges))
	np.save('edges/edges_'+str(t)+'.npy', edges)
	del edges
	#return edges
print('edges')

st = time.time()

cmd = "rm -r edges"
os.system(cmd)
cmd = "mkdir edges"
os.system(cmd)

pool = mp.Pool()
#pair_lst= 
pool.map(foo2, np.arange(shape[0]))
pool.close()
pool.join()
del pool


print((time.time()-st)/60)

print('edges done')

st = time.time()

graph_vtk1 = vtkMutableDirectedGraph()

points1 = vtkPoints()

weights1 = vtk.vtkDoubleArray()
weights1.SetNumberOfComponents(1)
weights1.SetName('Cluster Size')

weights2 = vtk.vtkDoubleArray()
weights2.SetNumberOfComponents(1)
weights2.SetName('Cluster Number')

weights3 = vtk.vtkDoubleArray()
weights3.SetNumberOfComponents(1)
weights3.SetName('Time')


max_label=0

for t in range(shape[0]-1):
	cluster_rep = np.load('vol/cluster_rep'+str(t)+'.npy', allow_pickle=True).item()
	cluster_rep1 = np.load('vol/cluster_rep'+str(t+1)+'.npy', allow_pickle=True).item()
	edges = np.copy(np.load('edges/edges_'+str(t)+'.npy', allow_pickle=True))
	for (p1,p2) in edges:
		(t1,cn1) = p1
		(t2,cn2) = p2

		if cluster_rep.get(cn1): (_,d1,lt1,ln1,cs1) = cluster_rep[cn1]
		else: continue
		if cluster_rep1.get(cn2): (_,d2,lt2,ln2,cs2) = cluster_rep1[cn2]
		else: continue

		x1 = ln_origin+(resolution*int(ln1))
		y1 = lt_origin+(resolution*int(lt1))

		x2 = ln_origin+(resolution*int(ln2))
		y2 = lt_origin+(resolution*int(lt2))

		vertex1 = graph_vtk1.AddVertex()
		points1.InsertNextPoint([x1, y1, -d1])
		weights1.InsertNextValue(cs1)
		weights2.InsertNextValue(t1*max_label+cn1)
		weights3.InsertNextValue(t1)
		vertex2 = graph_vtk1.AddVertex()
		points1.InsertNextPoint([x2, y2, -d2])
		weights1.InsertNextValue(cs2)
		weights2.InsertNextValue(t2*max_label+cn2)
		weights3.InsertNextValue(t2)
		graph_vtk1.AddEdge (vertex1, vertex2)

graph_vtk1.SetPoints(points1)
graph_vtk1.GetVertexData().AddArray(weights1);
graph_vtk1.GetVertexData().AddArray(weights2);
graph_vtk1.GetVertexData().AddArray(weights3);

graphToPolyData = vtkGraphToPolyData()
graphToPolyData.SetInputData(graph_vtk1)
graphToPolyData.Update()
writer = vtkXMLPolyDataWriter()
writer.SetInputData(graphToPolyData.GetOutput())
writer.SetFileName('computedTracks.vtp')
writer.Write()

print((time.time()-st)/60)


print('done\n********************\ntotal time = ',(time.time()-start)/60)

