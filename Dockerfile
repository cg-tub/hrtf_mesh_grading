# to build and run use:
# docker build --tag ubuntu:hrt-mesh-grading .
# docker run -dit --name hrt-mesh-grading ubuntu:hrt-mesh-grading /bin/bash

FROM ubuntu:20.04

# All commands are run from this path
WORKDIR /home

# Configure tzdata and timezone problems appear during `apt-get install cmake`
#ENV TZ=Europe/Berlin
#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# install required dependencies (remove specific versions if desired)
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y cmake \
                   make \
                   build-essential\
                   libx11-dev \
                   libxrandr-dev \
                   libxinerama-dev \
                   libxcursor-dev \
                   libxi-dev \
                   libgl1-mesa-dev \
                   libglu1-mesa-dev \
                   libeigen3-dev

COPY pmp-library pmp-library

# build the pmp-library
RUN cd pmp-library && mkdir build && cd build && cmake .. && make && make install

# add libpmp to the search path
RUN echo /usr/local/lib > /etc/ld.so.conf.d/local.conf
RUN ldconfig
