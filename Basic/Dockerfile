# Setting the base image.
FROM python:3.7-alpine

# Creating the maintainer.
MAINTAINER abhigyani

# Setting up the workdirectory.
WORKDIR /code

# Setting up environment variables.
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0

# Copy the requirements.txt
COPY . .

# Run the command to set up flask and redis.
RUN pip install -r requirements.txt

# Expose ports
EXPOSE 5000

# Command to run the flask.
CMD ["flask","run"]


