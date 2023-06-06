FROM render/extras

RUN apt-get update \
    && apt-get install -y libta-lib-dev
