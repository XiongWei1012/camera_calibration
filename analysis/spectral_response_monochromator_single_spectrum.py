"""
Plot a single spectrum generated with a monochromator, e.g. from a single
grating/filter setting.

This script is intended as a quick check of data quality in case the main
monochromator processing scripts do not work or produce unexpected results.

Command line arguments:
    * `folder`: folder containing monochromator data. This should contain NPY
    stacks of monochromator data taken at different wavelengths with a single
    settings (e.g. filter/grating).
"""

import numpy as np
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
save_to_data = savefolder/f"monochromator_{label}_data.pdf"
save_to_SNR = savefolder/f"monochromator_{label}_SNR.pdf"

# Load the data
spectrum = spectral.load_monochromator_data(root, folder)
print("Loaded data")

# Split the spectrum into its constituents
wavelengths = spectrum[:,0]
mean = spectrum[:,1:5]
stds = spectrum[:,5:]

# Plot the raw spectrum
spectral.plot_monochromator_curves(wavelengths, [mean], [stds], title=f"{camera.name}: Raw spectral curve ({label})", unit="ADU", saveto=save_to_data)
print("Saved raw spectrum plot")

# Calculate the signal-to-noise ratio (SNR) and plot it
SNR = mean / stds
SNR_err = np.zeros_like(SNR)  # don't plot errors on the SNR

spectral.plot_monochromator_curves(wavelengths, [SNR], [SNR_err], title=f"{camera.name}: Signal-to-noise ratio ({label})", unit="SNR", saveto=save_to_SNR)
print("Saved SNR plot")
