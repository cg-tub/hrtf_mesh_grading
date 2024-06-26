"""
Test the `hrtf_mesh_grading` binary inside a docker container.
- Start Docker desktop
- Set `build_container` flag below
- Run pytest in parent directory.

Initialization does the following
1. Connect to a docker client
2. Stop and remove existing containers named `docker_name` (settings below)
3. Build image with tag `docker_tag` if `build_container=True` (settings below)
4. Run container
5. Copy and compile local pmp-library if `compile_pmp=True` (settings below)
6. Run tests inside the container

Test files are written to the folder `test_data`.
"""
# %%
import pytest
import os
import shutil
import docker
import trimesh
import numpy as np
import numpy.testing as npt
from requests.exceptions import HTTPError

# test settings (adjust to your needs) ----------------------------------------

# build the docker container
# (required if it does not exist, takes a couple of minutes)
build_container = False
# Set to False if the container is already running to speed up repeated testing
run_container = False
# Copy and compile local pmp-library.
compile_pmp = False
# Do a complete new compile
make_clean = False

# tag and name of the docker container
docker_tag = 'ubuntu:hrt-mesh-grading'  # used for building the container
docker_name = 'hrt-mesh-grading'        # used for running the container


# helper functions ------------------------------------------------------------
def exec(container, command, out=True):
    """
    Run one or more commands inside a docker container.

    Parameters
    ----------
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


def stop_and_remove_container(client):
    """
    Stop and remove container.

    Must be done before running it but not if it is already running.
    """
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
    # pmp library for development
    "pmp-dev": os.path.join(current, '..', 'pmp-library'),
    # mounting point for meshes inside docker container
    "mount": '/home/data',
    # mounting point for pmp-dev inside the container
    "mount-pmp": '/home/pmp-dev'
}

del current

# make test dir
if not os.path.isdir(folders["test"]):
    os.mkdir(folders["test"])

# copy input mesh to temporary directory
shutil.copyfile(os.path.join(folders["input"], 'head.ply'),
                os.path.join(folders["test"], 'head_mm.ply'))

# generate a version of the head with unit meter
head = trimesh.load_mesh(os.path.join(folders["test"], "head_mm.ply"))
head.vertices *= 0.001
head.export(os.path.join(folders["test"], "head_m.ply"))

del head


# docker handling -------------------------------------------------------------
# start docker client
client = docker.from_env()

# build container
if build_container:

    stop_and_remove_container(client)

    print('\nBuilding the docker image (this might take some minutes)')
    image, log = client.images.build(
        path=folders["docker"], tag=docker_tag, rm=True)


# run the container
if run_container:
    # newly run the container
    stop_and_remove_container()

    print('\nStarting the container')
    container = client.containers.run(
        image=docker_tag,
        name=docker_name,
        command='/bin/bash',
        volumes={folders["test"]: {
                    "bind": folders["mount"], "mode": "rw"},
                 folders["pmp-dev"]: {
                    "bind": folders["mount-pmp"], "mode": "rw"}},
        detach=True,
        tty=True)
else:
    # get already running container
    container = client.containers.get(docker_name)


#  compile local pmp-library --------------------------------------------------
if compile_pmp:
    print('\nCompiling local pmp-library')

    command = ['rm -r pmp-library', 'cp -r pmp-dev pmp-library',
               'cd pmp-library', 'mkdir -p build', 'cd build', 'cmake ..']
    if make_clean:
        command.append('make clean')

    command.append('make -j && make install')
    command = ' && '.join(command)

    exit_code, output = exec(container, command, False)


# tests -----------------------------------------------------------------------
def test_help():
    """
    Test output for help parameter
    """
    print('\nTesting help message')

    # remeshing command
    command = "hrtf_mesh_grading"

    # remesh
    exit_code, output = exec(container, command, False)

    # check exit code
    assert exit_code == 1

    # check output
    lines = ['Example usage', '-x', '-y', '-e', '-s', '-l, r', '-g, h', '-m',
             '-i', '-o', '-v', '-b', 'Note', '[1] T. Palm',
             '[2] H. Ziegelwanger']
    for line in lines:
        assert line in output


@pytest.mark.parametrize('input_file', ['head_mm.ply', 'head_m.ply'])
@pytest.mark.parametrize('output_file', [
    'head_remeshed_hybrid_left_1_10.ply',
    'head_remeshed_hybrid_right_1_10.ply',
    'head_remeshed_distance_left_1_10.ply',
    'head_remeshed_distance_right_1_10.ply'])
def test_grading_against_reference(input_file, output_file):
    """
    Remesh reference mesh given in m and mm and compare results to reference.
    """

    # get remeshing parameters
    mode, side, l_min, l_max = output_file.split('_')[-4:]
    l_max = l_max.split('.')[0]

    # remeshing command
    command = (f"hrtf_mesh_grading -x {l_min} -y {l_max} -s {side} "
               f"-m {mode} "
               f"-i {folders['mount']}/{input_file} "
               f"-o {folders['mount']}/{output_file} ")

    # remesh
    exit_code, output = exec(container, command, False)

    # check exit code
    assert exit_code == 0

    # load result and reference
    test = trimesh.load_mesh(os.path.join(folders["test"], output_file))
    ref = trimesh.load_mesh(os.path.join(folders["reference"], output_file))

    # scale result if required
    if input_file.endswith('_m.ply'):
        test.vertices *= 1000

    # check results with 1/1000 mm tolerance
    npt.assert_almost_equal(test.vertices, ref.vertices, 3)


def test_verbosity():
    """
    Check the command line output in verbose mode
    """

    lines = [
        'input:', 'output:', 'mode: hybrid', 'side:', 'min. edge length: ',
        'max. edge length: ', 'max. error: ', 'gamma scaling left/right',
        'estimated ear channel entrance left',
        'estimated ear channel entrance right',
        'Faces before remeshing: ', 'Faces after remeshing: ']

    # use with verbosity
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    for line in lines:
        assert line in output

    # use without verbosity
    command = (f"hrtf_mesh_grading -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    for line in lines:
        assert line not in output


def test_error_value():
    """
    Test default and user value for error parameter `-e`
    """

    # use with default error
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    assert "max. error: 1" in output

    # use with custom error
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -e 2 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0
    assert "max. error: 2" in output


def test_gamma_parameters():
    """
    Test default and user value for gamma parameter `-g` and `-h`
    """

    # use with default gamma parameters
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.15/0.15" in output
    assert "estimated ear channel entrance left:   65.4298" in output
    assert "estimated ear channel entrance right: -68.3508" in output
    assert "after remeshing:  13950" in output

    # use with left ear custom gamma parameter
    command = ("hrtf_mesh_grading -v -x 1 -y 10 -s 'left' -g 0.18 "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.18/0.15" in output
    assert "estimated ear channel entrance left:   59.6963" in output
    assert "estimated ear channel entrance right: -68.3508" in output
    assert "after remeshing:  13830" in output

    # use with right ear custom gamma parameter
    command = ("hrtf_mesh_grading -v -x 1 -y 10 -s 'left' -h 0.2 "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.15/0.2" in output
    assert "estimated ear channel entrance left:   65.4298" in output
    assert "estimated ear channel entrance right: -58.795" in output
    assert "after remeshing:  13942" in output

    # use with two custom gamma parameters
    command = ("hrtf_mesh_grading -v -x 1 -y 10 -g 0 -s 'left' -g 0.18 -h 0.2 "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "gamma scaling left/right: 0.18/0.2" in output
    assert "estimated ear channel entrance left:   59.6963" in output
    assert "estimated ear channel entrance right: -58.795" in output
    assert "after remeshing:  13858" in output


def test_custom_ear_channel_entries():
    """Test hybrid grading with custom ear channel entries"""

    # use with default gamma parameters
    command = (f"hrtf_mesh_grading -v -x 1 -y 10 -s 'left' -l 60 -r -60 "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)

    assert exit_code == 0
    assert "ear channel entrance left:   60" in output
    assert "ear channel entrance right: -60" in output
    assert "estimated" not in output


def test_writing_binray_files():
    """
    Test writing results as text and binary files and compare results
    """

    # write as text file
    command = (f"hrtf_mesh_grading -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_remeshed_binary-false.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 0

    # write as binary file
    command = (f"hrtf_mesh_grading -b -x 1 -y 10 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
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


def test_assertions():
    """
    Test assertions for incorrect calls of hrtf_mesh_grading
    """

    # use with min edge length -x
    command = (f"hrtf_mesh_grading -y 10 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 1
    assert 'Example usage' in output

    # use with max edge length -y
    command = (f"hrtf_mesh_grading -x 1 -s left "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 1
    assert 'Example usage' in output

    # use with side -s
    command = (f"hrtf_mesh_grading -x 1 -y 10 "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 1
    assert 'Example usage' in output

    # use with invalid mode -m
    command = (f"hrtf_mesh_grading -x 1 -y 10 -s left -m hyper "
               f"-i {folders['mount'] + '/head_mm.ply'} "
               f"-o {folders['mount'] + '/head_tmp.ply'} ")

    exit_code, output = exec(container, command, False)
    assert exit_code == 134
    assert "Invalid mode! Mode must be 'hybrid' or 'distance'" in output
