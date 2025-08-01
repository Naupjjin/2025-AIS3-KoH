FROM debian:bookworm-slim

RUN apt update && apt install make g++ python3 python3-pip -y
WORKDIR /koh
COPY dashboard/ dashboard/
COPY simulator/ simulator/

RUN cd simulator && make
RUN cd dashboard && pip3 install -r requirements.txt --break-system-packages

EXPOSE 48763
CMD ["python3", "/koh/dashboard/app.py"]
