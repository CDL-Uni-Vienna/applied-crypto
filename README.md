# Applied (Quantum-)Cryptography
How to use Jupyter Notebooks for the exercises

## General Notes
The goal of this exercises is to give you a sense on what developing cryptographic algorithms means in practice, give you hands-on experiences besides the shiny theories in the course and make you aware of some issues, pitfalls that appear when it comes to implementation of cryptography.

To let you concentrate on the actual exercises and to keep the hurdles low, we provide Jupyter notebooks  running with current Python. The Jupyter notebooks will include the actual exercises as well as space to develop your solution straightaway.

Some of the cryptographic schemes you are going learn throughout the course require complex mathematical functions that are not covered by standard python libraries but require non-standard packages to be installed on your operating system. 

We defined a Docker -Image which includes all necessary libraries together with a Jupyter service that will be updated if necessary. The following will explain how you can use the Docker Image locally or by using the cloud service mybinder.org . If you prefer installing the required libraries on your host operating system, the last part of this How-To will lead you to the respective sources.

The current Dockerfile will always be available in the following git repository, which additionally includes all jupyter notebooks (in the subfolder notebook). The jupyter notebooks itself will additionally be published on Moodle.

(https://github.com/CDL-Uni-Vienna/applied-crypto.git)[https://github.com/CDL-Uni-Vienna/applied-crypto.git]

**We wish you lots of fun with the exercises :-)**

## 1	Running the Docker on your local device

We strongly encourage you to try out this method, as we cannot guarantee the availability of the cloud service that will be explained in the next section.
1.	Download and install docker for your operating system:
  a.	Windows: https://docs.docker.com/docker-for-windows/install/
  b.	Ubuntu: https://docs.docker.com/engine/install/ubuntu/
  c.	Mac: https://docs.docker.com/docker-for-mac/install/
2.	(Optional) Download and install git 
  a.	Alternative: You can also just download zip-file from the git-repository 
  b.	https://git-scm.com/book/en/v2/Getting-Started-Installing-Git 
3.	Open a command prompt, cd’ to your working directory directory. In many operating system, you can simply browse to a folder and “right-click”->”open in terminal”
4.	Clone the git repository:
  ```git clone https://github.com/CDL-Uni-Vienna/applied-crypto.git```
5.	Browse to the folder, you just cloned (if you downloaded the zip-file from github, just browse to the extracted folder)
  ```cd applied-crypto```
6.	Build the docker image. On some operating systems, you may have to run this command as root (this might take a bit):
  ```docker build --build-arg NB_USER=jovyan --build-arg NB_UID=1000 -t applied-crypto . ```
7.	Run the docker container On some operating systems, you may have to run this command as root:
  ```docker run -p 8888:8888 applied-crypto jupyter notebook --ip=0.0.0.0 --port=8888```
  - If you wish to access the jupyter notebooks on your local hard disk, you can run the docker command as follows:
    ```docker run -v <full path to your notebooks>:/home/jovyan/notebooks/mount -p 8888:8888 moderncrypto jupyter notebook --ip=0.0.0.0 --port=8888```
8.	Your command prompt should output something similar to the following:
```
To access the server, open this file in a browser:
        file:///home/jovyan/.local/share/jupyter/runtime/jpserver-1-open.html
    Or copy and paste one of these URLs:
        http://ebca97460388:8888/tree?token=01871d37b8eeb0f5ad012bc58cdc32c8dcbe861917b1b290
        http://127.0.0.1:8888/tree?token=01871d37b8eeb0f5ad012bc58cdc32c8dcbe861917b1b290
```

10.	Copy this url, open your browser and paste the url in the address bar and you should be redirected to a jupyter notebook, which contains all notebooks downloaded from the git repository

## 2	Running the Jupyter notebook with mybinder.org
mybinder.org allows running docker containers as a cloud service, and thereby offers a very easy solution to run the provided docker images. Typically, if an image was built before by someone else, the containers are built quickly and you can start just straightaway. However, starting the service just takes a while sometimes, so stay patient (or use method 1 ;-) )

1.	Visit https://mybinder.org 
2.	Make sure the dropdown box shows “GitHub”
3.	Enter the path to the git repository
4.	Enter the git branch main
5.	Enter the name of the notebook with the current exercise. (Optional, if you don’t enter it you will just see a folder with all exercises)
6.	Press Launch and wait

*Note: Sometimes the notebooks are not writeable, if that’s the case just download it or save it under a different name.*

## 3	Self installation of required libraries
You can certainly install all required libraries on your host operating system or on a virtual machine. You find the required python libraries in the ```requirements.txt``` file in the repository. 




