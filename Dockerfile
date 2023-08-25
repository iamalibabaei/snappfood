FROM python:3.10-alpine

# ENVs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

# Working Dir
RUN mkdir /task
WORKDIR /task

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt /task/requirements.txt
RUN pip install -r requirements.txt

# Copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /task/entrypoint.sh
RUN chmod +x /task/entrypoint.sh

# Copy project
COPY . .

# Run entrypoint
ENTRYPOINT ["sh", "/task/entrypoint.sh"]