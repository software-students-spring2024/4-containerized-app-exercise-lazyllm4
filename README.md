![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
![machine_learning_client CI/CD](https://github.com/software-students-spring2024/4-containerized-app-exercise-lazyllm4/actions/workflows/machine_learning_client.yml/badge.svg)
![web_app CI/CD](https://github.com/software-students-spring2024/4-containerized-app-exercise-lazyllm4/actions/workflows/web_app.yml/badge.svg)



# To build:

From the root dir
enter following command
`docker compose up --build`

# Run Docker container:

1. In one terminal

`docker network create project4`

`cd machine_learning_client`

`docker build -t web_app_image .`



2. start a new terminal

`cd web_app`

`docker build -t ml_client_image .`

3. start the last terminal

`docker run --name mongodb -d -p 27017:27017 --network project4 mongo`
# Smart Home Security App
Our Smart Home Security App combines user-friendly access controls with advanced security features to enhance home safety. Users can log in using a username and password, while an integrated facial recognition system verifies identities against a database of known faces for additional security. The app also includes a sophisticated motion detection system that identifies and records any activity, alerting homeowners to potential intruders. Designed for ease of use, it seamlessly integrates with a wide range of cameras and home automation systems, making it an ideal solution for enhancing residential security through technology.

- **Web App:** Get if not detected motion from database and display website and login page
- **Machine Learning Client:** Python program that do facial recognition and motion detector
- **Database:** A MongoDB database stores if not detected motion, userid, password, photo




## Contributors
1. [Angel Wu](https://github.com/angelWu2002)	
2. [Weilin Cheng](https://github.com/M1stery232)
3. [Ruichen Wang](https://github.com/rcwang937)	
4. [Haoyang Li](https://github.com/LeoLi727)	
