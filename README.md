# Curvature-adaptive mesh grading for numerical approximation of head-related transfer functions

Head-related transfer functions (HRTFs) describe the direction dependent free field sound propagation from a point source to the listener's ears and are an important tool for audio in virtual and augmented reality. Classically, HRTFs are measured acoustically with the listener being positioned in the center of a spherical loudspeaker array. Alternatively, they can be approximated by numerical simulation, for example applying the boundary element method (BEM) to a piece wise linear representation (a surface mesh) of the listener's head. Numerical approximation may be more economical, particularly in combination with methods for the synthesis of head geometry. To decrease the computation time of the BEM, it has been suggested to gradually decrease the resolution of the mesh with increasing distance from the ear for which the HRTF is approximated. We improve this approach by also considering the curvature of the geometry. The resulting graded meshes lead to faster simulation with the same or better accuracy in the HRTF compared to previous work.

## References

https://cg-tub.github.io/hrtf_mesh_grading/

[T. Palm, S. Koch, F. Brinkmann, and M. Alexa, “Curvature-adaptive mesh grading for numerical approximation of head-related transfer functions,” DAGA 2021, Vienna, Austria, pp. 1111–1114.](https://www.researchgate.net/publication/356264260_Curvature-adaptive_mesh_grading_for_numerical_approximation_of_head-related_transfer_functions)

## Getting Started

### Clone the repository

```sh
git clone --recursive https://github.com/cg-tub/hrtf_mesh_grading.git
```

Note that recursive cloning requires SSH key and we recommend that you [generating it](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) and [adding it to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account). If you do not want to do this. You can separately clone

```sh
git clone https://github.com/cg-tub/hrtf_mesh_grading.git
cd hrtf-mesh-hrtf_mesh_grading
git clone --recursive https://github.com/cg-tub/pmp-library.git
```

### Configure and build

There are two options for building the project from which you can chose:

**1. Locally**

Build the project locally on your machine. This could work on Linux, MacOS, and
Windows, however, we only test on Linux. Note that this requires the dependencies
listed at [PMP-Library installation](https://www.pmp-library.org/installation.html)
together with more detailed instructions for installation.

```sh
cd pmp-library && mkdir build && cd build && cmake .. && make
```

**2. Docker Container**

Build a docker container to run the mesh-grading inside the container. Note that
this requires [Docker](https://www.docker.com/). To build and run the container
use

```sh
docker build --tag ubuntu:hrt-mesh-grading .
docker run -dit --name hrt-mesh-grading ubuntu:hrt-mesh-grading /bin/bash
```

### Remeshing

The binary for remeshing is located at
```sh
pmp-library/build/hrtf_mesh-grading
```

After it has been added to you search path, e.g., via a symbolic link
```sh
ln -s pmp-library/build/hrtf_mesh-grading /usr/local/bin
```

it can be used via
```sh
hrtf-mesh-grading -x 0.5 -y 10 -s "left" -i data/head.ply -o data/head_graded_left.ply
```

For more information call
```sh
hrtf-mesh-grading
```
without any parameters.

## License

The code is provided under a simple and flexible MIT-style
license, thereby allowing for both open-source and commercial usage.

## Differences of forked version

For implementing the HRTF mesh grading, changes in SurfaceRemeshing.cpp and MeshProcessingViewer.cpp have been made and `hrtf-mesh-grading` was added to `pmp-library/src/apps`.
