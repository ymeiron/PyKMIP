FROM python:3.14.4-trixie
WORKDIR /root
COPY . pykmip
RUN \
  pip install --no-cache-dir --requirement pykmip/docker/requirements.txt && \
  pip install --no-cache-dir --no-deps ./pykmip && \
  pip install --no-cache-dir --no-deps slugs==1.1.0 && \
  mv pykmip/docker/run.sh . && \
  mv pykmip/docker/config /etc/pykmip && \
  rm -rf pykmip
EXPOSE 5696
CMD ["/bin/bash", "/root/run.sh"]