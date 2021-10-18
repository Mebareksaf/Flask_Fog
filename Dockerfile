FROM djx339/docker-python-opencv-ffmpeg:py3-cv3.4.0

WORKDIR /app

ADD ./requirements.txt ./

RUN pip install setuptools && \
pip install opencv-python==4.0.0.21 && \
pip install -r requirements.txt

ADD ./ ./

#CMD ["python3", "app.py"] 
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
