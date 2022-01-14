# Curvature-adaptive mesh grading for numerical approximation of head-related transfer functions

Head-related transfer functions (HRTFs) describe the direction dependent free field sound propagation from a point source to the listener's ears and are an important tool for audio in virtual and augmented reality. Classically, HRTFs are measured acoustically with the listener being positioned in the center of a spherical loudspeaker array. Alternatively, they can be approximated by numerical simulation, for example applying the boundary element method (BEM) to a piece wise linear representation (a surface mesh) of the listener's head. Numerical approximation may be more economical, particularly in combination with methods for the synthesis of head geometry. To decrease the computation time of the BEM, it has been suggested to gradually decrease the resolution of the mesh with increasing distance from the ear for which the HRTF is approximated. We improve this approach by also considering the curvature of the geometry. The resulting graded meshes lead to faster simulation with the same or better accuracy in the HRTF compared to previous work.

## References

https://cg-tub.github.io/hrtf_mesh_grading/

[T. Palm, S. Koch, F. Brinkmann, and M. Alexa, “Curvature-adaptive mesh grading for numerical approximation of head-related transfer functions,” DAGA 2021, Vienna, Austria, pp. 1111–1114.](https://www.researchgate.net/publication/356264260_Curvature-adaptive_mesh_grading_for_numerical_approximation_of_head-related_transfer_functions)

## Getting Started

Although the PMP library can also be used on Windows and MacOS, we only support
Linux. There are two options for getting started with the HRTF mesh grading:

1. Clone the repository and locally build the code
2. Use a pre-compiled docker image (requires [docker](https://www.docker.com/))

Both options will make the `hrtf_mesh_grading` tool available as explained in

3. HRTF mesh grading

### 1. Clone and build locally
**Clone the repository**

```sh
git clone --recursive https://github.com/cg-tub/hrtf_mesh_grading.git
```

Note that recursive cloning requires SSH key and we recommend that you [generating it](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) and [adding it to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account). If you do not want to do this. You can separately clone

```sh
git clone https://github.com/cg-tub/hrtf_mesh_grading.git
cd hrtf_mesh_grading
git clone --recursive https://github.com/cg-tub/pmp-library.git
```

**Configure and build**

There are two options for building the project from which you can chose:

*Locally*

Build the project locally on your machine. This could work on Linux, MacOS, and
Windows, however, we only test on Linux. Note that this requires the dependencies
listed at [PMP-Library installation](https://www.pmp-library.org/installation.html)
together with more detailed instructions for installation.

```sh
cd pmp-library && mkdir build && cd build && cmake .. && make
```

*Docker Container*

Build a docker container to run the mesh-grading inside the container. Note that
this requires [Docker](https://www.docker.com/). To build and run the container
use

```sh
docker build --tag ubuntu:hrtf-mesh-grading .
docker run -dit --name hrtf-mesh-grading ubuntu:hrtf-mesh-grading /bin/bash
```

### 2. Use pre-compiled docker image

Pull the docker image with

```sh
docker pull fabrin/hrtf-mesh-grading
```

### 3. Mesh preparation

Please note that the mesh grading tool expects the mesh to meet the following requirements
- The interaural center must be in the origin of coordinates. The interaural center is the midpoint between the axis that passes through the left and right ear channel entrances.
- The mesh must be viewing in positive x-direction with the y-axis acting as the interaural axis, i.e., the left ear is pointing in positive y-direction.
- The unit of the mesh must be millimeter.

If you are using Blender for exporting meshes, make sure to apply all transforms before exporting, export only the selected object, and use the settings `Forward: Y Forward` and `Up: Z up` during export.

### 4. HRTF mesh grading

The binary for remeshing is located at
```sh
pmp-library/build/hrtf_mesh_grading
```

**Mesh grading without docker**

Add it to you search path, e.g., via a symbolic link
```sh
ln -s pmp-library/build/hrtf_mesh_grading /usr/local/bin
```

Use the mesh grading via
```sh
hrtf_mesh_grading -x 0.5 -y 10 -s "left" -i data/head.ply -o data/head_graded_left.ply
```

Call without any parameters for getting the complete description
```sh
hrtf_mesh_grading
```

**Mesh grading with docker**

In this case you need to run the docker container before you start with the mesh grading.
This can be done with
```sh
docker run -dit --name hrtf-mesh-grading -v '</local/folder>:/home/data' <tag> /bin/bash
```

- `</local/folder>` should be the absolute path to a folder on your disc containing
the meshes for grading, e.g., the `data` folder inside this repository (without `<` and `>`).
- `<tag>` is the tag of the docker container. If you followed *1 Clone and build locally* it is `ubuntu:hrtf-mesh-grading`. If you followed *2 Use pre-compiled docker image* it is `fabrin/hrtf-mesh-grading`.

Once the container is running, you have different options for using it
- use the [exec command](https://docs.docker.com/engine/reference/commandline/exec/), e.g., `docker exec hrtf-mesh-grading hrtf_mesh_grading` (Note that hrtf-mesh-grading is the name of the container and hrtf_mesh_grading the command to be executed)
- use the [Python API](https://docker-py.readthedocs.io/en/stable/)
- Start the container's command line interface from the [Docker Desktop app](https://www.docker.com/products/docker-desktop).

For more examples see *Mesh grading without docker*.

## License

The code is provided under a simple and flexible MIT-style
license, thereby allowing for both open-source and commercial usage.

## Differences to forked version

The following changes were made to the original [PMP library](https://github.com/pmp-library/pmp-library)

- HRTF remeshing algorithm was added to
`pmp-library/src/pmp/algorithms/SurfaceRemeshing.cpp`

- `pmp-library/src/apps/MeshProcessingViewer.cpp` was updated to include the
HRTF remeshing algorithm

- The command line application `pmp-library/src/apps/hrtf-mesh-grading` was
added. It calls `SurfaceRemeshing.cpp`

- The command line application was added to `pmp-library/src/apps/CMakeList.txt`

# Maintainance

Some reminders for the developers.

To update the pmp-library submodule use
```sh
git submodule update --remote pmp-library
```

Manualy compile hrtf-mesh-grading command line application
```sh
g++ hrtf-mesh-grading.cpp -o hrtf-mesh-grading -I /usr/include/eigen3/ /usr/local/lib/libpmp.so
```

To update the docker image on hub.docker run
```sh
docker build -t fabrin/hrtf-mesh-grading .
docker pull fabrin/hrtf-mesh-grading
```

Running the tests requires
```sh
conda install docker-py numpy
pip install trimesh
```
