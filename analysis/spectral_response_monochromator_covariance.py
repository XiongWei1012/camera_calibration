"""
Analyse the covariances between spectral response data at different wavelengths
in a single monochromator run.

Command line arguments:
    * `folder`: folder containing monochromator data. This should contain NPY
    stacks of monochromator data taken at different wavelengths with a single
    settings (e.g. filter/grating).
"""

import numpy as np
from matplotlib import pyplot as plt
from sys import argv
from spectacle import io, spectral

# Get the data folder from the command line
folder = io.path_from_input(argv)
root = io.find_root_folder(folder)
label = folder.stem

# Load Camera object
camera = io.load_camera(root)
print(f"Loaded Camera object: {camera}")

# Save locations
savefolder = camera.filename_analysis("spectral_response", makefolders=True)
save_to_SNR = savefolder/f"monochromator_{label}_SNR_cov.pdf"
save_to_cov = savefolder/f"monochromator_{label}_covariance.pdf"
save_to_SNR_G = savefolder/f"monochromator_{label}_SNR_cov_G_mean.pdf"
save_to_cov_G = savefolder/f"monochromator_{label}_covariance_G_mean.pdf"

# Find the filenames
mean_files = sorted(folder.glob("*_mean.npy"))

# Half-blocksize, to slice the arrays with
blocksize = 100
d = blocksize//2

# Empty arrays to hold the output
wvls  = np.zeros((len(mean_files)))
means = np.zeros((len(mean_files), 4, (blocksize+1)**2))

# Loop over all files
print("Wavelengths [nm]:", end=" ", flush=True)
for j, mean_file in enumerate(mean_files):
    # Load the mean data
    m = np.load(mean_file)

    # Bias correction
    m = camera.correct_bias(m)

    # Flat-field correction
    m = camera.correct_flatfield(m)

    # Demosaick the data
    mean_RGBG = camera.demosaick(m)

    # Select the central blocksize x blocksize pixels
    midx, midy = np.array(mean_RGBG.shape[1:])//2
    sub = mean_RGBG[:,midx-d:midx+d+1,midy-d:midy+d+1]
    sub = sub.reshape(4, -1)

    # NaN if a channel's mean value is near saturation
    sub[sub >= 0.95 * camera.saturation] = np.nan

    # Store results
    means[j] = sub
    wvls[j] = mean_file.stem.split("_")[0]

    print(wvls[j], end=" ", flush=True)

# Reshape array: sort by filter first, then by wavelength
# First len(wvls) elements are R, then G, then B, then G2
means_RGBG2 = np.concatenate([means[:,0], means[:,1], means[:,2], means[:,3]])

# Indices to select R, G, B, and G2
R, G, B, G2 = [np.s_[len(wvls)*j : len(wvls)*(j+1)] for j in range(4)]
RGBG2 = [R, G, B, G2]

# Calculate mean SRF and covariance between all elements
srf = np.nanmean(means_RGBG2, axis=1)
srf_cov = np.cov(means_RGBG2)

# Calculate the variance (ignoring covariance) from the diagonal elements
diag = np.where(np.eye(len(wvls) * 4))
srf_var = srf_cov[diag]
srf_std = np.sqrt(srf_var)

# Plot the SRFs with their standard deviations, variance, and SNR
labels = ["Response\n[ADU]", "Variance\n[ADU$^2$]", "SNR"]
fig, axs = plt.subplots(nrows=3, sharex=True, figsize=(4,4))
for ind, c in zip(RGBG2, "rybg"):
    axs[0].plot(wvls, srf[ind], c=c)
    axs[0].fill_between(wvls, srf[ind]-srf_std[ind], srf[ind]+srf_std[ind], color=c, alpha=0.3)

    axs[1].plot(wvls, srf_var[ind], c=c)

    axs[2].plot(wvls, srf[ind]/srf_std[ind], c=c)

for ax, label in zip(axs, labels):
    ax.set_ylabel(label)
    ax.set_ylim(ymin=0)

axs[-1].set_xlim(wvls[0], wvls[-1])
axs[-1].set_xlabel("Wavelength [nm]")

axs[0].set_title(folder.stem)

plt.savefig(save_to_SNR, bbox_inches="tight")
plt.show()
plt.close()

# Plot the covariances
ticks = [(ind.start + ind.stop) / 2 for ind in RGBG2]
ticklabels = [f"${c}$" for c in ["R", "G", "B", "G_2"]]

plt.figure(figsize=(5,5))
plt.imshow(srf_cov, cmap="cividis")
plt.colorbar(label="Covariance")
plt.xticks(ticks, ticklabels)
plt.yticks(ticks, ticklabels)
plt.title(f"Covariances in {folder.stem}")
plt.savefig(save_to_cov, bbox_inches="tight")
plt.show()
plt.close()

# Plot an example
for c, ind in zip("rgby", RGBG2):
    plt.plot(wvls, srf_cov[G,ind][0], c=c)
plt.xlabel("Wavelength [nm]")
plt.ylabel("Covariance")
plt.ylim(ymin=0)
plt.xlim(wvls[0], wvls[-1])
plt.show()
plt.close()

# Calculate mean of G and G2
I = np.eye(len(wvls))
M_G_G2 = np.zeros((len(wvls)*3, len(wvls)*4))
M_G_G2[R,R] = I
M_G_G2[B,B] = I
M_G_G2[G,G] = 0.5*I
M_G_G2[G,G2] = 0.5*I

srf_G = M_G_G2 @ srf
srf_G_cov = M_G_G2 @ srf_cov @ M_G_G2.T

diag = np.where(np.eye(len(wvls) * 3))
srf_G_var = srf_G_cov[diag]
srf_G_std = np.sqrt(srf_G_var)

# Plot the SRFs with their standard deviations, variance, and SNR
labels = ["Response\n[ADU]", "Variance\n[ADU$^2$]", "SNR"]
fig, axs = plt.subplots(nrows=3, sharex=True, figsize=(4,4))
for ind, c in zip(RGBG2[:3], "rgb"):
    axs[0].plot(wvls, srf_G[ind], c=c)
    axs[0].fill_between(wvls, srf_G[ind]-srf_G_std[ind], srf_G[ind]+srf_G_std[ind], color=c, alpha=0.3)

    axs[1].plot(wvls, srf_G_var[ind], c=c)

    axs[2].plot(wvls, srf_G[ind]/srf_G_std[ind], c=c)

for ax, label in zip(axs, labels):
    ax.set_ylabel(label)
    ax.set_ylim(ymin=0)

axs[-1].set_xlim(wvls[0], wvls[-1])
axs[-1].set_xlabel("Wavelength [nm]")

axs[0].set_title(folder.stem)

plt.savefig(save_to_SNR_G, bbox_inches="tight")
plt.show()
plt.close()

# Plot the covariances
ticks, ticklabels = ticks[:3], ticklabels[:3]

plt.figure(figsize=(5,5))
plt.imshow(srf_G_cov, cmap="cividis")
plt.colorbar(label="Covariance")
plt.xticks(ticks, ticklabels)
plt.yticks(ticks, ticklabels)
plt.title(f"Covariances in {folder.stem} (mean $G, G_2$)")
plt.savefig(save_to_cov_G, bbox_inches="tight")
plt.show()
plt.close()

