from matplotlib import pyplot as plt
import numpy as np
import rawpy
from cv2 import resize
from scipy.ndimage.filters import gaussian_filter1d as gauss
from sys import argv
from scipy.optimize import curve_fit

filename = argv[1]

RGB = ["r", "g", "b"]
TLpeaks = np.array([436.6, 487.7, 544.45, 611.6])

col0 = 1501
col1 = 1911
col2 = 1949
col3 = 2315

row0 = 2300
row1 = 3750

img = rawpy.imread(filename)
data = img.postprocess(use_camera_wb=True, gamma=(1,1), output_bps=8)
#data_res = resize(data, (data.shape[1]//n, data.shape[0]//n))

thick = data[row0:row1, col0:col1]
thin  = data[row0:row1, col2:col3]

for D in (thick, thin):
    plt.imshow(D)
    plt.show()

def gauss_filter(D, sigma=7, *args, **kwargs):
    """
    Apply a 1-D Gaussian kernel along the wavelength axis
    """
    return gauss(D.astype(float), sigma, *args, axis=0, **kwargs)

thickF = gauss_filter(thick)
thinF  = gauss_filter(thin )

for D in (thickF, thinF):
    plt.imshow(D.astype("uint8"))
    plt.show()

for D, DF in zip([thick, thin], [thickF, thinF]):
    for d in (D, DF):
        for j in (0,1,2):
            plt.plot(d[:, 100, j], c=RGB[j])
        plt.xlim(0, d.shape[0])
        plt.ylim(0,255)
        plt.show()

def find_3peaks(D):
    return D.argmax(axis=0)

for DF in [thickF, thinF]:
    peaks = find_3peaks(DF)
    for j in (0,1,2):
        plt.plot(peaks[:, j], c=RGB[j])
    plt.xlim(0, DF.shape[1])
    plt.ylim(0, DF.shape[0])
    plt.show()

def wavelength(coords, a, b, c, d):
    x, y = coords
    return a*x + b*y**2 + c*y + d

peaks_thick = find_3peaks(thickF)
peaks_thin = find_3peaks(thinF)
y = np.concatenate((np.arange(col0, col1), np.arange(col2, col3)))
p = np.concatenate((peaks_thick, peaks_thin))
p_fit = p.copy()
for j in (0,1,2):
    coeff = np.polyfit(y, p[:,j], 2)
    p_fit[:,j] = np.polyval(coeff, y)

coeffarr = np.tile(np.nan, (y.shape[0], 2))
wvlfit = np.tile(np.nan, (y.shape[0], 3))
for i, col in enumerate(y):
    coeffarr[i] = np.polyfit(p_fit[i], TLpeaks[[3,2,0]], 1)
    wvlfit[i] = np.polyval(coeffarr[i], p_fit[i])