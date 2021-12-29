#!/bin/bash
conda install -c conda-forge -y julia
julia -e 'using Pkg; Pkg.add("IJulia")'
julia -e 'using Pkg; Pkg.add("Plots")'
