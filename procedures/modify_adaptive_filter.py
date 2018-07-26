from scipy.signal import butter, filtfilt
import numpy as np
import statistics
from sigman.analyzer import InvalidArgumentError

procedure_type = 'modify'
description = """The procedure perform adaptive filtering of the signal. Algorithm in same way average signal according to cardiac cycle.
Every sample is calculated as:
y[i] = w'*x
where: x - vector contains subsequent harmonic of the signal
    w - weight vector

After every iteration weight vector is adapted according to equation:
W = W + 2 * u * (a[i] -y[i])*x'
a[i] - signal sample
u - Time constant

Filter was described in this paper: 
Kardec Allan "Filtering Noncorrelated Noise in Impedance Cardiography" (1995)
Laguna Pablo "Adaptive Filter for Event-Related Bioelectric Signals Using an Impulse Correlated Reference Input" (1992) 

"""
author = 'mzylinski'
arguments = {
    'u':"Time constant use to correct weight vector"
}
default_arguments = {'u':'0.05'}
required_points = ['R']

def referenceSignal (signalLength, sampleNumber):
    H = int(np.floor(signalLength/2)-1)
    p = np.sqrt (H)
    x = np.matrix(np.zeros(H*2))
    for i in range (1,H*2+1):
        if (np.mod(i,2)== 0):
            x[0,i-1] = (1/p)*np.cos(2*3.14*((i-1)*sampleNumber/signalLength))
        else:
            x[0,i-1] = (1/p)*np.sin(2*3.14*((i)*sampleNumber/signalLength))
    return x

def weighterWector (X,a):
    P = a*X.T
    R = X*X.T
    W = P/R
    return W.T

def maxMatrixLength (Rx):
    maxDifrence = 0
    pom = 0;
    for i in range (1,len(Rx)):
        dt = Rx[i]-Rx[i-1]
        if (dt>maxDifrence):
            maxDifrence = dt
            pom = i
    return maxDifrence



def procedure(wave, points, begin_time, end_time, arguments):
    u = arguments['u']
    R = points['R']
    data = wave.data_slice(begin_time, end_time)
    SR = np.floor(wave.sample_rate)
    N = int((R.data_x[1]-begin_time)*SR)
    
    #maxLength = int(np.floor(maxMatrixLength (R.data_x)*wave.sample_rate))+1
    #maxH = int(np.floor(maxLength/2)-1)
    X = []
    W = []
   
    #for i in range (1,maxLength):
     #   x = referenceSignal (maxLength, i)
      #  X.append(x)
    result = np.array(np.zeros(len(data)))
    result[0:N] = data[0:N]
  
    for j in range (0,(len(R.data_x)-1)):
        a = data[int(( R.data_x[j]*SR)):int(np.floor(R.data_x[j+1]*SR))]

        H = int(np.floor(len(a)/2)-1)   
        
        for i in range(0,len(a)):
            
            if (i >= len (W)):
                x = referenceSignal (len(a), i+1)
                X.append(x)
                #nw = np.matrix(np.zeros(maxH*2))
                #nw = weighterWector (xp,a[i]) 
                
                #nw [0,0:(2*H)]=w
                w = weighterWector (x,a[i])
                W.append(w)
            else:
                xp = X[i]
                x = xp[0,0:(2*H)]
                wp = W[i]
                w = wp[0,0:(2*H)]

            
            if (N  >= len(data)):
                 break
            result[N] = x*w.T
           
            errorEstimate = a[i] - result[N]
            
            newW = W[i]
            newW[0,0:(2*H)]= w + ((2*u*errorEstimate)*x)
            W[i] = newW 
            N = N + 1
        
    result [N:len(data)] = data [N:len(data)]    
    return result

def interpret_arguments(wave, points, arguments):
    "Sprawdza, czy podane argumenty są poprawne."
    #u
    try:
        u = float(arguments['u'])
    except:
        InvalidArgumentError("Invalid filter order "
                                   "{}".format(arguments['u']))
 

    return {'u':u,}

def execute(wave, points,  begin_time, end_time, arguments):
    arguments = interpret_arguments(wave, points,  arguments)
    return procedure(wave, points, begin_time, end_time, arguments)

