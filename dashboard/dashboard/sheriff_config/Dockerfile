FROM gcr.io/google-appengine/python

RUN virtualenv /env -p python3
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

ADD requirement_pybind11.txt /app/requirement_pybind11.txt
ADD requirement_google-re2.txt /app/requirement_google-re2.txt
ADD requirements.txt /app/requirements.txt

# We need libre2-dev and pybind11 used for installing google-re2
RUN apt-get update && apt-get install -y libre2-dev && \
    pip install --require-hashes -r requirement_pybind11.txt && \
    export RE2_INCLUDES=$(python -c 'import pybind11; print(pybind11.get_include());') && \
    export CFLAGS="-I${RE2_INCLUDES} -std=c++11" && \
    pip install --require-hashes -r requirement_google-re2.txt

RUN pip install --require-hashes -r requirements.txt --no-deps

ADD . /app

ENTRYPOINT gunicorn -b :$PORT main:APP --workers 6