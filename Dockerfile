FROM docker.heinrichhartmann.net:5000/python3.8

RUN apt-get -y install imagemagick
# Fix https://bugs.archlinux.org/task/60580
COPY policy.xml /etc/ImageMagick-6/policy.xml

# Install distributed package
COPY /dist /dist
RUN cd /dist; pip install *.whl

RUN mkdir -p /work
WORKDIR /work
