#! /usr/bin/env python
"""Generate static images summarizing the Freesurfer reconstruction.

This script is part of the lyman packges. LYMAN_DIR must be defined.

USAGE: anatomy_snapshots.py <subject arg>

The subject arg can be one or more subject IDs, name of subject file, or
path to subject file. Running with no arguments will use the default
subjects.txt file in the lyman directory.

Dependencies:
- Nibabel
- PySurfer

The resulting files can be most easily viewed using the Ziegler app.

"""
import os
import os.path as op
import sys

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import nibabel as nib
from mayavi import mlab
from surfer import Brain

import lyman


def main(arglist):

    # Find the subjects for this execution
    if not arglist:
        arglist = None
    subjects = lyman.determine_subjects(arglist)

    # Find the project details
    proj = lyman.gather_project_info()
    data_dir = proj["data_dir"]

    # Make images for each subject
    for subj in subjects:

        # Make sure the output directory exists
        out_dir = op.join(data_dir, subj, "snapshots")
        if not op.exists(out_dir):
            os.mkdir(out_dir)

        # Plot the surfaces
        for hemi in ["lh", "rh"]:
            b = Brain(subj, hemi, "inflated", curv=False, offscreen=False,
                      config_opts=dict(background="white",
                                       width=800, height=500))

            for view in ["lat", "med"]:
                b.show_view(view)
                mlab.view(distance="auto")
                png = op.join(out_dir, "%s.surface_%s.png" % (hemi, view))
                b.save_image(png)
        b.close()

        # Plot the volume slices
        brain_file = op.join(data_dir, subj, "mri/brainmask.mgz")
        brain_data = nib.load(brain_file).get_data()
        ribbon_file = op.join(data_dir, subj, "mri/ribbon.mgz")
        ribbon_data = nib.load(ribbon_file).get_data().astype(float)
        ribbon_data[ribbon_data == 3] = 1
        ribbon_data[ribbon_data == 42] = 1
        ribbon_data[ribbon_data != 1] = np.nan

        # Find the limits of the data
        # note that FS conformed space is not (x, y, z)
        xdata = np.flatnonzero(brain_data.any(axis=1).any(axis=1))
        xmin, xmax = xdata.min(), xdata.max()
        ydata = np.flatnonzero(brain_data.any(axis=0).any(axis=0))
        ymin, ymax = ydata.min(), ydata.max()
        zdata = np.flatnonzero(brain_data.any(axis=0).any(axis=1))
        zmin, zmax = zdata.min() + 5, zdata.max() - 15

        # Figure out the plot parameters
        n_slices = (zmax - zmin) // 3
        n_row, n_col = n_slices // 8, 8
        start = n_slices % n_col // 2 + zmin
        figsize = (10, 1.375 * n_row)
        slices = (start + np.arange(zmax - zmin))[::3][:n_slices]

        # Draw the slices and save
        vmin, vmax = 0, 100
        f, axes = plt.subplots(n_row, n_col, figsize=figsize, facecolor="k")
        cmap = mpl.colors.ListedColormap(["#C41E3A"])
        for i, ax in enumerate(reversed(axes.ravel())):
            i = slices[i]
            ax.imshow(np.flipud(brain_data[xmin:xmax, i, ymin:ymax].T),
                      cmap="gray", vmin=vmin, vmax=vmax)
            ax.imshow(np.flipud(ribbon_data[xmin:xmax, i, ymin:ymax].T),
                      cmap=cmap, vmin=.05, vmax=1.5, alpha=.8)
            ax.set_xticks([])
            ax.set_yticks([])

        out_file = op.join(data_dir, subj, "snapshots/volume.png")
        plt.savefig(out_file, dpi=100, bbox_inches="tight",
                    facecolor="k", edgecolor="k")
        plt.close(f)



if __name__ == "__main__":

    # Usage exit
    if any(set(sys.argv) & {"-h", "-help", "--help"}):
        print __doc__
        sys.exit()

    main(sys.argv[1:])