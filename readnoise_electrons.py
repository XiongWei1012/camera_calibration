import numpy as np
from sys import argv
from matplotlib import pyplot as plt
from phonecal import raw, plot, io
from phonecal.general import gaussMd

folder = io.path_from_input(argv)
root, images, stacks, products, results = io.folders(folder)
results_readnoise = results/"readnoise"

isos, stds  = io.load_stds  (folder, retrieve_value=io.split_iso)
colours     = io.load_colour(stacks)

gain_table = np.load(products/"gain_lookup_table.npy")

low_iso = isos.argmin()
high_iso= isos.argmax()

for iso, std in zip(isos, stds):
    gain = gain_table[1, iso]
    std  *= gain

    gauss = gaussMd(std, sigma=10)
    std_RGBG, _= raw.pull_apart(std, colours)
    gauss_RGBG = gaussMd(std_RGBG, sigma=(0,5,5))
    vmin, vmax = gauss_RGBG.min(), gauss_RGBG.max()
    
    plot.hist_bias_ron_kRGB(std_RGBG, xlim=(0, 25), xlabel="Read noise (e$^-$)", saveto=results_readnoise/f"electrons_histogram_iso{iso}.png")
    
    plot.show_image(gauss, colorbar_label="Read noise (e$^-$)", saveto=results_readnoise/f"electrons_gauss_iso{iso}.png")
    for j, c in enumerate("RGBG"):
        X = "2" if j == 3 else ""
        plot.show_image(gauss_RGBG[j], colorbar_label="Read noise (e$^-$)", saveto=results_readnoise/f"electrons_{c}{X}_gauss_iso{iso}.png", colour=c, vmin=vmin, vmax=vmax)
    print(iso)