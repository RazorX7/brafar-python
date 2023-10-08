#FROM ubuntu
#MAINTAINER Linna Xie <xieln@smail.nju.edu.cn>
#
## Install basic dependencies
#RUN apt-get update && apt-get install -y --no-install-recommends pkg-config git python-dev-is-python3 gcc wget vim zip ca-certificates
#
## Install anaconda3
#RUN mkdir /home/linna
#RUN cd /home/linna/ && wget --no-check-certificate https://repo.anaconda.com/archive/Anaconda3-2023.07-2-Linux-x86_64.sh && chmod 777 ./Anaconda3-2023.07-2-Linux-x86_64.sh && ./Anaconda3-2023.07-2-Linux-x86_64.sh -b -p /home/linna/conda
#RUN echo "export PATH=/home/linna/conda/bin:$PATH" >> ~/.bashrc
#RUN export PATH=/home/linna/conda/bin:$PATH && pip install --upgrade pip && pip install psutil zss autopep8 python-Levenshtein astunparse prettytable apted fastcache
#
## Set workdir
#WORKDIR /home/linna
#RUN mkdir /home/linna/brafar-python
#COPY brafar-python /home/linna/brafar-python
##RUN git clone https://github.com/githubhuyang/refactory.git

FROM faucet/python3
WORKDIR /home/linna
RUN mkdir /home/linna/brafar-python
RUN pip install zss
RUN pip install timeout_decorator
COPY brafar-python /home/linna/brafar-python