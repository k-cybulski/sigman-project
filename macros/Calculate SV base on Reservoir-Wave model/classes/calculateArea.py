import numpy as np

class calculateArea:
    def calculate (Pex, dt = 0.001):
        area = 0
        if len(Pex)>2:
            start = calculateArea.maximum (Pex[0:round(len(Pex)/2)])
            mean = np.mean (Pex[0:round(len(Pex)*0.66)])
            if (mean < 0):
                mean = 0
            if (start is not 0):
                i = start-1
                while (Pex[i]>mean):
                    area = area + (((Pex[i]+Pex[i+1])/2)*dt)
                    i = i - 1
                    if (i == 0):
                        break
            if (start<(len(Pex)-2)):
                i = start + 1
                while (Pex[i]>mean):
                    area = area + (((Pex[i]+Pex[i-1])/2)*dt)
                    i = i + 1
                    if (i == (len(Pex)-1)):
                        break

        return area

    def maximum (data):
        if len(data)>0:
            m = max (data)
            itemindex = np.where(data==m)[0]
            if (len(itemindex)>1):
                wynik = itemindex[len(itemindex)-1]
            else:
                wynik = itemindex[0]
            return wynik
        else:
            return 0