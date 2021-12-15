# to build and run use:
# docker build --tag ubuntu:hrt-mesh-grading .
# docker run -dit --name hrt-mesh-grading ubuntu:hrt-mesh-grading /bin/bash

FROM ubuntu:20.04

# All commands are run from this path
WORKDIR /home

# Configure tzdata and timezone (need during `apt install cmake`)
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# install required dependencies (remove specific versions if desired)
RUN apt update
RUN apt upgrade -y
RUN apt install -y cmake=3.16.3-1ubuntu1 \
                   make=4.2.1-1.2 \
                   build-essential=12.8ubuntu1 \
                   libx11-dev=2:1.6.9-2ubuntu1.1 \
                   libxrandr-dev=2:1.5.2-0ubuntu1 \
                   libxinerama-dev=2:1.1.4-2 \
                   libxcursor-dev=1:1.2.0-2 \
                   libxi-dev=2:1.7.10-0ubuntu1 \
                   libgl1-mesa-dev=20.2.6-0ubuntu0.20.04.1 \
                   libglu1-mesa-dev=9.0.1-1build1 \
                   libeigen3-dev=3.3.7-2

COPY pmp-library pmp-library

# build the pmp-library
RUN cd pmp-library && mkdir build && cd build && cmake .. && make && make install

# add libpmp to the search path
RUN echo /usr/local/lib > /etc/ld.so.conf.d/local.conf
RUN ldconfig
