"""
Test the `hrtf_mesh_grading` binary inside a docker container. Start Docker
Desktop and cd into this folder before running this script.

After defining the test settings the following is done
1. Connect to a docker client
2. Stop and remove existing containers named `docker_name` (settings below)
3. Build image with tag `docker_tag` if `build_container=True` (settings below)
4. Run container
5. Run tests inside the container

Test files are written to the folder `test_data`.
"""
# %%
import os
import shutil
import glob
import docker
import trimesh
import numpy as np
import numpy.testing as npt
from requests.exceptions import HTTPError

# test settings (adjust to your needs) ----------------------------------------

# build the docker container
# (required if it does not exist, takes a couple of minutes)
build_container = False

# tag and name of the docker container
docker_tag = 'ubuntu:hrt-mesh-grading'  # used for building the container
docker_name = 'hrt-mesh-grading'        # used for running the container

# select tests
test_against_reference = True
test_verbosity = True
test_error_value = True
test_gamma_parameters = True
test_custom_ear_channel_entries = True
test_writing_binray_files = True
test_assertions = True


# tests (do not adjust) -------------------------------------------------------

# start docker client
client = docker.from_env()


# function for running code inside container conveniently
def exec(container, command, out=True):
    """
    Run one or more commands inside a docker container.

    Paremters
    ---------
    container : docker container
    command : str or list of commands. Multiple commands are joined with ' && '
    out : print the output from running the commands
    """
    # convert to list
    if not isinstance(command, list):
        command = [command]

    # run the command
    command = ' && '.join(command)
    result = container.exec_run(f"sh -c '{command}'")

    # show the
    if out:
        print(result.output.decode())

    return result.exit_code, result.output.decode()


# directory and data handling -------------------------------------------------

current = os.path.dirname(os.path.abspath(__file__))

folders = {
    # directory for writing test data
    "test": os.path.join(current, 'test_data'),
    # directory containing the dockerfile
    "docker": os.path.join(current, '..'),
    # directory containing input data for testing
    "input": os.path.join(current, '..', 'data'),
    # directory containing references for testing
    "reference": os.path.join(current, 'references'),
    # mounting point inside docker container
    "mount": '/home/data'
}

del current

# make test dir
if not os.path.isdir(folders["test"]):
    os.mkdir(folders["test"])

# copy input mesh to temporary directory
shutil.copyfile(os.path.join(folders["input"], 'head.ply'),
                os.path.join(folders["test"], 'head.ply'))


# stop and remove container ---------------------------------------------------
print('\nStopping the container')
try:
    client.containers.get(docker_name).stop()
    print(f'- stopped existing container {docker_name}')
except HTTPError:
    print(f'- container {docker_name} already stopped or not existing')

try:
    client.containers.get(docker_name).remove()
    print(f'- removed existing container {docker_name}')
except HTTPError:
    print(f'- container {docker_name} already removed or not existing')


# build container -------------------------------------------------------------
if build_container:

    print('\nBuilding the docker image (this might take some minutes)')
    image, log = client.images.build(
        path=folders["docker"], tag=docker_tag, rm=True)


# run the container -----------------------------------------------------------
print('\nStarting the container')
container = client.containers.run(
    image=docker_tag,
    name=docker_name,
    command='/bin/bash',
    volumes={folders["test"]: {"bind": folders["mount"], "mode": "rw"}},
    detach=True,
    tty=True)


# tests -----------------------------------------------------------------------
if test_against_reference:
    """
    Remesh reference mesh as meshes in test_data and compare results.
    """
    print('\nTesting against the references')

    files = glob.glob(os.path.join(folders["reference"], '*.ply'))

    for file in files:
        file = os.path.basename(file)
        print(f"- {file}")

        # get remeshing parameters
        side, l_min, l_max = file.split('_')[-3:]
        l_max = l_max.split('.')[0]

        # remeshing command
        command = (f"hrtf_mesh_grading -x {l_min} -y {l_max} -s {side} "
                   f"-i {folders['mount'] + '/head.ply'} "
                   f"-o {folders['mount'] + '/' + file} ")

        # remesh
        exit_code, output = exec(container, command, False)

        # check exit code
        assert exit_code == 0

        # compare result to reference
        test = trimesh.load_mesh(os.path.join(folders["test"], file))
        ref = trimesh.load_mesh(os.path.join(folders["reference"], file))

        # check results with 1/1000 mm tolerance
        npt.assert_almost_equal(test.vertices, ref.vertices, 3)

    del files, file, side, l_min, l_max, command, exit_code, output, test, ref


if test_verbosity:
    """
    Check the command line output in verbose mode
    """
    print('\nTest verbosity')

    lines = ['input:', 'output:', 'side:', 'min. edge length: ',
             'max. edge length: ', 'max. error: ', 'gamma scaling left/right',
             'estimated ear channel entrance left',
             'estimated ear channel entrance right',
             'Faces before remeshing: ', 'Faces after remeshing: ']

    # use with verbosity
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    for line in lines:
        assert line in output

    # use without verbosity
    command = (f"hrtf_mesh_grading -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    for line in lines:
        assert line not in output

    del command, exit_code, output, lines, line


if test_error_value:
    """
    Test default and user value for error parameter `-e`
    """
    print('\nTest error parameter')

    # use with default error
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    assert "max. error: 1" in output

    # use with custom error
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -e 2 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    assert "max. error: 2" in output

    del command, exit_code, output


if test_gamma_parameters:
    """
    Test default and user value for gamma parameter `-g` and `-h`
    """
    print('\nTest gamma parameters')

    # use with default gamma parameters
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.15/0.15" in output
    assert "estimated ear channel entrance left:   65.4298" in output
    assert "estimated ear channel entrance right: -68.3508" in output
    assert "after remeshing:  13950" in output

    # use with left ear custom gamma parameter
    command = ("hrtf_mesh_grading -v -x 1 -y 10 -s 'left' -g 0.18 "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.18/0.15" in output
    assert "estimated ear channel entrance left:   59.6963" in output
    assert "estimated ear channel entrance right: -68.3508" in output
    assert "after remeshing:  13830" in output

    # use with right ear custom gamma parameter
    command = ("hrtf_mesh_grading -v -x 1 -y 10 -s 'left' -h 0.2 "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.15/0.2" in output
    assert "estimated ear channel entrance left:   65.4298" in output
    assert "estimated ear channel entrance right: -58.795" in output
    assert "after remeshing:  13942" in output

    # use with two custom gamma parameters
    command = ("hrtf_mesh_grading -v -x 1 -y 10 -g 0 -s 'left' -g 0.18 -h 0.2 "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.18/0.2" in output
    assert "estimated ear channel entrance left:   59.6963" in output
    assert "estimated ear channel entrance right: -58.795" in output
    assert "after remeshing:  13858" in output

    del command, exit_code, output


if test_custom_ear_channel_entries:
    print('\nTest custom ear channel entries')

    # use with default gamma parameters
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s 'left' -l 60 -r -60 "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "ear channel entrance left:   60" in output
    assert "ear channel entrance right: -60" in output
    assert "estimated" not in output

    del command, exit_code, output


if test_writing_binray_files:
    """
    Test writing results as text and binary files and compare results
    """
    print('\nTest writing binary files')

    # write as text file
    command = (f"hrtf_mesh_grading -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_remeshed_binary-false.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0

    # write as binary file
    command = (f"hrtf_mesh_grading -b -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_remeshed_binary-true.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0

    # compare mesh
    text = trimesh.load_mesh(
        os.path.join(folders["test"], "head_remeshed_binary-false.ply"))
    binary = trimesh.load_mesh(
        os.path.join(folders["test"], "head_remeshed_binary-true.ply"))

    npt.assert_allclose(np.sort(text.vertices, 0),
                        np.sort(binary.vertices, 0),
                        atol=0.01)  # 0.01 mm tolerance

    # compare filesize
    assert \
        os.path.getsize(os.path.join(
            folders["test"], "head_remeshed_binary-false.ply")) > \
        os.path.getsize(os.path.join(
            folders["test"], "head_remeshed_binary-true.ply"))

    del command, exit_code, output, text, binary


if test_assertions:
    """
    Test assertions for incorrect calls of hrtf_mesh_grading
    """
    print('\nTesting assertions')

    # use with min edge length -x
    command = (f"hrtf_mesh_grading -y 10 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 1
    assert 'Example usage' in output

    # use with max edge length -y
    command = (f"hrtf_mesh_grading -x 1 -s left "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 1
    assert 'Example usage' in output

    # use with side -s
    command = (f"hrtf_mesh_grading -x 1 -y 10 "
               f"-i {folders['mount'] + '/head.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 1
    assert 'Example usage' in output
