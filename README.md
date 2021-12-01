# Curvature-adaptive mesh grading for numerical approximation of head-related transfer functions

Head-related transfer functions (HRTFs) describe the direction dependent free field sound propagation from a point source to the listener's ears and are an important tool for audio in virtual and augmented reality. Classically, HRTFs are measured acoustically with the listener being positioned in the center of a spherical loudspeaker array. Alternatively, they can be approximated by numerical simulation, for example applying the boundary element method (BEM) to a piece wise linear representation (a surface mesh) of the listener's head. Numerical approximation may be more economical, particularly in combination with methods for the synthesis of head geometry. To decrease the computation time of the BEM, it has been suggested to gradually decrease the resolution of the mesh with increasing distance from the ear for which the HRTF is approximated. We improve this approach by also considering the curvature of the geometry. The resulting graded meshes lead to faster simulation with the same or better accuracy in the HRTF compared to previous work. 

## Website and Documentation 

https://cg-tub.github.io/hrtf_mesh_grading/

## Getting Started

Clone the repository:

```sh
git clone --recursive https://github.com/cg-tub/hrtf_mesh_grading.git
```

Configure and build:

```sh
cd pmp-library && mkdir build && cd build && cmake .. && make
```

Run the mesh processing app:

```sh
./mpview ../example_models/head.ply
```
