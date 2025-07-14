import re
import sys
import matplotlib.pyplot as plt
import numpy as np
import mplcursors as mpc
import matplotlib.colors as mcolors


path = "./data/"
# inputfiles=["one core","two cores","four cores","eight cores"]
# inputfiles=["np1","np2","np4","np8"] #five times streamtracer
# inputfiles=["d31","d32","d34","d38"] #five times streamtracer with d3
# inputfiles=["d3unstructured1","d3unstructured2","d3unstructured4","d3unstructured8"] #five times streamtracer with d3 unstructured
# inputfiles= ["np4", "d34", "d3unstructured4"]
inputfiles=["np1","np2","np3","np4","np5","np6","np7","np8"] #five times streamtracer
inputfiles=["d31","d32","d33","d34","d35","d36","d37","d38"] #five times streamtracer with d3
inputfiles=["d3unstructured1","d3unstructured2","d3unstructured3","d3unstructured4","d3unstructured5","d3unstructured6","d3unstructured7","d3unstructured8"] #five times streamtracer with d3 unstructured
# inputfiles=["exec2","exec4","exec8"] #five3 times streamtracer with paraview's mpiexec
inputfiles=["exec2","exec3","exec4","exec5","exec6","exec7","exec8"] #five3 times streamtracer with paraview's mpiexec
inputfiles=["pathline2","pathline4","pathline6","pathline8"] #five3 times streamtracer with paraview's mpiexec
inputfiles=["seedplacement1","seedplacement2","seedplacement3","seedplacement4","seedplacement5","seedplacement6","seedplacement7","seedplacement8"]
# inputfiles=["seedplacement5"]
# inputfiles=["np2","np4","np8","exec2","exec4","exec8"]
inputfiles=["streamtracerfivetimes2", "streamtracerfivetimes4", "streamtracerfivetimes8","streamtracerfivetimes16","streamtracerfivetimes32"]
inputfiles=["fivestreamtracer_np_1", "fivestreamtracer_np_2", "fivestreamtracer_np_4", "fivestreamtracer_np_8", "fivestreamtracer_np_16", "fivestreamtracer_np_32"]
# inputfiles=["streamtracerfivetimes32"]
# inputfiles=["streamtracerfivetimes4gpu","streamtracerfivetimes8gpu","streamtracerfivetimes16gpu"]
inputfiles=['pathlines_np_1', 'pathlines_np_2', 'pathlines_np_4', 'pathlines_np_8', 'pathlines_np_16', 'pathlines_np_32']
            
            # pathlinesbob_np_48, pathlinesbob_np_64, pathlinesbob_np_8, pathlinesbob_np_80, pathlinesbob_np_96


# inputfiles=['streamlinesfive_np_paraviewmpi_2','streamlinesfive_np_paraviewmpi_4','streamlinesfive_np_paraviewmpi_8','streamlinesfive_np_paraviewmpi_16','streamlinesfive_np_paraviewmpi_32']

inputfiles=['streamlinesfive_np_paraviewmpi_2','streamlinesfive_np_paraviewmpi_4','streamlinesfive_np_paraviewmpi_8','streamlinesfive_np_paraviewmpi_16','streamlinesfive_np_paraviewmpi_32','streamlinesfive_np_paraviewmpi_48','streamlinesfive_np_paraviewmpi_64','streamlinesfive_np_paraviewmpi_80','streamlinesfive_np_paraviewmpi_96']

inputfiles=['streamlinesfive_np_paraviewmpi_48','streamlinesfive_np_paraviewmpi_64','streamlinesfive_np_paraviewmpi_80','streamlinesfive_np_paraviewmpi_96','streamlinesfive_np_paraviewmpi_112','streamlinesfive_np_paraviewmpi_128','streamlinesfive_np_paraviewmpi_144','streamlinesfive_np_paraviewmpi_160',]

# inputfiles=['streamlinesfive_np_2','streamlinesfive_np_4','streamlinesfive_np_8','streamlinesfive_np_16','streamlinesfive_np_32']
            
# inputfiles = ['streamlinesfive_np_48','streamlinesfive_np_64','streamlinesfive_np_80','streamlinesfive_np_96']

inputfiles=['streamlinesfive_bigdataset_np_2','streamlinesfive_bigdataset_np_4','streamlinesfive_bigdataset_np_8','streamlinesfive_bigdataset_np_16','streamlinesfive_bigdataset_np_32','streamlinesfive_bigdataset_np_48','streamlinesfive_bigdataset_np_64','streamlinesfive_bigdataset_np_80','streamlinesfive_bigdataset_np_96','streamlinesfive_bigdataset_np_112','streamlinesfive_bigdataset_np_128','streamlinesfive_bigdataset_np_144','streamlinesfive_bigdataset_np_160']

# inputfiles=['streamlinesfive_np_paraviewmpi_96','streamlinesfive_np_paraviewmpi_96_3nodes','streamlinesfive_np_paraviewmpi_96_5nodes']

# inputfiles = ['small_isovol_2','small_isovol_4','small_isovol_8','small_isovol_16','small_isovol_32','small_isovol_48','small_isovol_64','small_isovol_80','small_isovol_96','small_isovol_112','small_isovol_128','small_isovol_144','small_isovol_160']

# inputfiles = ['big_isovol_2','big_isovol_4','big_isovol_8','big_isovol_16','big_isovol_32','big_isovol_48','big_isovol_64','big_isovol_80','big_isovol_96','big_isovol_112','big_isovol_128','big_isovol_144','big_isovol_160']

# queries=["Calculator1", "StreamTracer1", "Glyph1"]
queries=["StreamTracer1"]
queries=["IsoVolume1"]
# queries=["seedPlacement1", "Pathlines1"]
queries=["Calculator1"]
# queries = ["roms_bobhires"]
times = []
maxlen = 0
filters = []
filtertimes = []
filterlogs = []
markers =["o", "x", "^", "v", "^", "s", "h", "d", "1"]
# colours=["tab:blue","tab:orange","tab:green","tab:red","tab:purple","tab:pink"]
colours=[ "lightblue","lightskyblue", "deepskyblue", "dodgerblue", "royalblue", "blue", "darkblue", "black", "darkviolet", "violet" ]
colours = list(mcolors._colors_full_map.keys())
n = len(inputfiles)
q = len(queries)

mintimes = [[sys.float_info.max for _ in range(len(queries))] for _ in range(len(inputfiles))]
maxtimes = [[sys.float_info.min for _ in range(len(queries))] for _ in range(len(inputfiles))]

# print(mintimes)
# print(maxtimes)

for i in range(len(inputfiles)):
    filtertimes.append([])
    filterlogs.append([])

    for query in queries:
        filtertimes[i].append([])
        filterlogs[i].append([])


print((filtertimes))

def findinfo(searchstring, time, file, fileidx, queryidx):
    complicationstring = "move-data"
    # searchstring = r'{}'.format(searchstring_)
    # searchstring = "".join(["(?i)\b", filtername, "1*\b"])
    filter_ = re.findall(f"\s{searchstring}", file)
    complication = re.findall(f"\s{complicationstring}", file)
    if(len(filter_)>0 and len(complication) <= 0):
        filtertimes[fileidx][queryidx].append(time)
        filterlogs[fileidx][queryidx].append(file)
        mintimes[fileidx][queryidx] = min(mintimes[fileidx][queryidx], time)
        maxtimes[fileidx][queryidx] = max(maxtimes[fileidx][queryidx], time)


    else:
        filtertimes[fileidx][queryidx].append(None)
        filterlogs[fileidx][queryidx].append(None)

def isfloat(num):
    try:
        float(num)
        return True
    except:
        return False

for inputfileidx in range(len(inputfiles)):
    logs = open(path+inputfiles[inputfileidx], 'r+') #logs is a full file
    time=[]
    filtertime=[]
    # mintime = sys.float_info.max
    # maxtime = sys.float_info.min
    for log in logs: #log is a single line in a file
        time__ = re.findall(r"..\d\.\d\d\ds", log)
        # filter_ = re.findall(r"(?i)\bstreamtracer1*\b", log)
        # filter_ = re.findall(r"(?i)\bcalculator1+\b", log)
        if(len(time__) >0 and not time__[0].startswith('}') and isfloat(time__[0][:-1])):
            time_ = float(time__[0][:-1])
            for queryidx in range(len(queries)):
                findinfo(queries[queryidx], time_, log, inputfileidx, queryidx)
            time.append(time_)
    maxlen = max(maxlen, len(time))
    times.append(time)
    # print(len(filtertimes[0]))

# PLOT NOW



for time in times:
    if(len(time) < maxlen):
        time.extend(None for _ in range(maxlen - len(time)))

# for filter in filters:
#     if(len(filter) < maxlen):
#         filter.extend(None for _ in range(maxlen - len(filter)))

for filtertime in filtertimes:
    for filtert in filtertime:
        if(len(filtert) < maxlen):
            filtert.extend(None for _ in range(maxlen - len(filtert)))

for filterlog in filterlogs:
    for filterl in filterlog:
        if(len(filterl) < maxlen):
            filterl.extend(None for _ in range(maxlen - len(filterl)))

# print(len(filtertimes[0][0]))
# print(len(filtertimes[0][1]))
# print(len(filtertimes[1][0]))
# print(len(filtertimes[1][1]))
# for filtertime in filtertimes:
#     if(len(filtertime) < maxlen):
#         filtertime.extend(None for _ in range(maxlen - len(filtertime)))

x = [i for i in range(maxlen)]

# print(len(x), len(filtertimes), len(filtertimes[1]))
# print(filtertimes)



def plotwhole(x, ys, filtertimes, filterlogs):
    fig, ax = plt.subplots()
    for yidx in range(len(ys)):
        ax.plot(x,ys[yidx],c=colours[yidx])
    # for yfilter in yfilters:
    #     ax.scatter(x,yfilter, marker="x") # type: ignore
    scatterplots = []
    annotations = []
    for fileidx in range(len(filtertimes)):
        for queryidx in range(len(filtertimes[0])):
            sc = ax.scatter(x,filtertimes[fileidx][queryidx], marker=markers[queryidx], c=colours[fileidx], picker=True) # type: ignore
            # def selectionprinter(event):
            #     # lambda sel: sel.annotation.set_text()
            #     event.annotation.set_text(filterlogs[fileidx][queryidx][event.index])
            # mpc.cursor(sc).connect("add", lambda sel: print(sel.artist.get_label))
            # mpc.cursor(sc).connect("add", lambda sel: sel.annotation.set_text(filterlogs[fileidx][queryidx][sel.index]))
            scatterplots.append(sc)

    
    # for sc in zip(scatterplots):
    #     sc.set_picker(True)

    def on_pick(event):
        # line = event.artist
        # xdata, ydata = line.get_data()
        # ind = event.ind
        # print(event.artist.get_label())
        child = str(event.artist.get_label())
        number = int(child[6:])
        print(number)
        number = number - n
        fileidx = number // q
        queryidx = number % q
        print(n, q, fileidx, queryidx)

        # numbers = re.findall('[0-9]+', str)
        mpc.cursor(scatterplots).connect("add", lambda sel: sel.annotation.set_text(filterlogs[fileidx][queryidx][sel.index]))

    cid = fig.canvas.mpl_connect('pick_event', on_pick)

    
    plt.xlabel("Steps")
    plt.ylabel("Time(in seconds)")
    legendarray = inputfiles
    for fileidx in range(len(filtertimes)):
        for queryidx in range(len(filtertimes[0])):
            legendarray.append(queries[queryidx]+": " + f"{maxtimes[fileidx][queryidx]-mintimes[fileidx][queryidx]:.2f}")
    
    
    plt.legend(legendarray)
        # mplcursors.cursor(scatterplots).connect("add", lambda sel: sel.annotation.set_text(filterlogs[fileidx][queryidx][sel.index]))

    def onpick3(event):
        ind = event.ind
        label = event.artist.get_label()
        print('onpick3 scatter:', label, ind, x[ind])

    # fig.canvas.mpl_connect('pick_event', onpick3) 

    plt.show()

for i in range(len(inputfiles)):
    for j in range(len(queries)):
        print("time for " + queries[j] + " in "+ inputfiles[i] + " is from " + str(mintimes[i][j])+" to " + str(maxtimes[i][j])+ " : " +str(maxtimes[i][j]-mintimes[i][j]))

# print(mintimes, maxtimes)
def plotbars(inputfiles, mintimes, maxtimes, queries):

    barwidth = 0.20
    ind = np.arange(len(queries)) #number of groups
    heights = []

    maxt = np.array(maxtimes).transpose()
    mint = np.array(mintimes).transpose()
    heights = maxt-mint
    bars = []
    
    heights = heights.transpose()
    # np.round(heights,2)
    for fileidx in range(len(inputfiles)):
        bar = plt.bar(ind+barwidth*fileidx, heights[fileidx], barwidth, label = inputfiles[inputfileidx], color=colours[fileidx])
        plt.bar_label(bar,np.round(heights[fileidx], 2))
        bars.append(bar)

    plt.xlabel('Filter')
    plt.ylabel('Time(in sec)')
    plt.xticks(ind + barwidth*len(queries)/2, queries)
    plt.legend(bars, inputfiles)
    plt.show()



# plotbars(inputfiles, mintimes, maxtimes, queries)
plotbars_starttime(inputfiles,mintimes, maxtimes, queries)
# plotwhole(x,times, filtertimes, filterlogs)
# plotstackedbars(inputfiles, mintimes, maxtimes, queries)


    



def plotbars_starttime(inputfiles, mintimes, maxtimes, queries):

    barwidth = 0.20
    ind = np.arange(len(queries)) #number of groups
    heights = []

    maxt = np.array(maxtimes).transpose()
    mint = np.array(mintimes).transpose()
    heights = mint
    bars = []
    
    heights = heights.transpose()
    # np.round(heights,2)
    for fileidx in range(len(inputfiles)):
        bar = plt.bar(ind+barwidth*fileidx, heights[fileidx], barwidth, label = inputfiles[inputfileidx], color=colours[fileidx])
        plt.bar_label(bar,np.round(heights[fileidx], 2))
        bars.append(bar)

    plt.xlabel('Filter')
    plt.ylabel('Time(in sec)')
    plt.xticks(ind + barwidth*len(queries)/2, queries)
    plt.legend(bars, inputfiles)
    plt.show()
