# Work Tracker

Demo Project for BakerSoft GmbH Backend Developer Position Application. Consisting of a multi-user/multi-project work
tracking system presented as a RESTful API.

The application allows Users to create Entries
(manually or via a timer that can be paused) pertaining to a task they have been assigned, as well as viewing Entries
from Users involved in the same project.

The project itself is built using Django, Django REST Framework, PostgreSQL and
Docker as a containerization tool, with JWT tokens being used as Authentication method.

****
****

## Setting up the Project

### Repository

Firstly, you will have to clone the repository on to your local system by using:

**HTTPS**
```
$ git clone https://github.com/SE-KLING/work_tracker.git
```

Once you have successfully cloned the project on to your local system, you can move on to the Docker set-up.


### Docker

As mentioned before, a Docker container has been configured to allow for easy set-up of the application.
If you do not currently have Docker on your system, you can download Docker Desktop
[here](https://www.docker.com/products/docker-desktop/)‚ and install it using these instructions for either
[Mac](https://docs.docker.com/desktop/install/mac-install/), [Windows](https://docs.docker.com/desktop/install/windows-install/)
or [Linux](https://docs.docker.com/desktop/install/linux-install/).

Once Docker has been installed and is up and running, you can open the root project directory via your terminal and run
the following commands to firstly build and then run the docker container.

```shell
# If using an Apple Silicon machine, please specify the platform to be used as outlined below:
$ export DOCKER_DEFAULT_PLATFORM=linux/amd64

# Build the stack, this may take a while on the first run
$ docker-compose -f local.yml build --no-cache

# Start the docker engine
$ docker-compose -f local.yml up -d
```

Following the above, the container should now be running successfully.

**NOTE:**

> On start, migrations will have been made, a data dump loaded on to the database and the local server would have been
started, running on [http://0.0.0.0:8000/](http://0.0.0.0:8000/).

****
****

## About the Project Structure

### Project Models:
The Project consists of 5 main models:
- **User**: A User can be assigned to be part of one or more **Projects** and can be designated a **Task** from said
            projects. A User will then create **Entries** related to the **Tasks** to track the work they've done.


- **Company**: A **Company** will consist of one or more **Projects**.


- **Project**: A **Project** will be linked to a single **Company** and will consist of one or more **Tasks**.
               One or more users will be assigned to a specific **Project**.


- **Task**: A **Task** will be linked to a single **Company** as well as a single **User** and will consist of one or
            more **Entries** from the mentioned **User**.


- **Entry**: **Entries** are created to track time spent on a **Task** by the specific **User** of said **Task**.

![Work Tracker ERD](/work_tracker/static/images/diagrams/work_tracker_erd.jpeg?raw=true "Work Tracker ERD Diagram")

****
****

## Testing out Project Admin

Firstly, you may want to log in to the [admin](http://0.0.0.0:8000/admin/) site to authenticate the User via
Session authentication as well as taking a look at the preloaded data.

You can do so by using the preloaded **BakerSoft** admin user with the following credentials:
```python
credentials = {
    'email': bakersoft@admin.com,
    'password': BakerSoft24
}
```

After taking a look at the Admin site, you may want to look at the available APIs used to manage the
Work Tracker Application. You can access some basic API documentation [here.](http://0.0.0.0:8000/api/docs)
However, if wanting to thoroughly test the APIs, it is recommended to use [Postman](https://web.postman.co/) and the
attached collection.

****
****


## Testing out the APIs
As mentioned, a Postman collection(```work_tracker_postman_collection.json```), already containing mock requests with
viable data, has been created to allow for easy testing of the different API endpoints.

Additionally, more thorough documentation on how the endpoints function can be found there.

Information on importing the attached collection can be found
[here](https://learning.postman.com/docs/getting-started/importing-and-exporting-data/#importing-data-into-postman).

**NOTE:**

> In that the docker container is running on a new system, new AUTH tokens will have to be created and updated on the
> Postman requests.
> You can do this by using the ```/api/user/auth-token``` endpoint with the desired User credentials.
>
> Note that all User passwords are set as ```BakerSoft24``` for ease of use.
