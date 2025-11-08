<div align=center> <img src="../../other/img/logo.png" width=300 alt=" logo"> </div>

## <div align="center">Software Platform Construction </div> 
- ### __Installing System Software Required for Self-Driving Cars__

   - ### Self-Driving Car Operating System Installation Flowchart

   <div align=center>
   <img src="./img/Orin_System_Installation.jpg" width="100%" />
   </div>

   - ### Installing the Operating System on Nvidia Jetson Orin Nano

      - #### Preparation Before Installation
         - Please prepare or configure a physical host machine running the Ubuntu operating system. The use of any virtualization environment (such as a virtual machine) for executing the relevant tasks is strictly prohibited.
         - Please ensure that a Solid-State Drive (SSD) is properly installed on your Jetson Orin Nano.

      - #### NVIDIA SDK Manager Installation

         - Download [NVIDIA SDK Manager 2.3.0](https://developer.nvidia.com/sdk-manager)

          <div align=center><img src="./img/NVIDIA_SDK_Manager_Download_Page.png" width="80%"></div>

         - Double-click the installation package to install, and upon completion and successful login, launching the application will display the following screen.
   
      - #### JetPack Software Version Installation, Upgrade, and Downgrade Guide

         - SDK Manager is an official tool from NVIDIA that allows you to install, upgrade, or downgrade JetPack versions on Jetson devices. Before proceeding, please switch the Nvidia Jetson Orin Nano to Recovery Mode and follow the instructions to connect the power and establish a connection. Below is the operation procedure for SDK Manager.
         
         <div align=center><img src="./img/20250930_212433.jpg" width="80%" /></div>

      <div align=center>
<table>
<tr>
<th>Connect Host - Connect the Jetson Orin Nano controller to the Ubuntu host machine via a USB cable..</th>
<th>Confirm Connection - Verify that the Jetson Orin Nano is successfully connected and recognized by the SDK Manager.</th>
<th>Select Dev Kit - Select the target Developer Kit in the interface.</th>
</tr>
<tr>
<td><img src="./img/11.jpg" width=400 /></td>
<td><img src="./img/12.png" width=400 /></td>
<td><img src="./img/13.png" width=400 /></td>
</tr>
<tr>
<th>Choose Version - Select the desired JetPack version from the menu for installation or downgrade.</th>
<th>Check Options - Check the required software components on the left side (such as OS, SDKs), and click "Next".</th>
<th>Enter Password - Enter the administrator password as prompted.</th>
</tr>
<tr>
<td><img src="./img/14.png" width=400 /></td>
<td><img src="./img/15.png" width=400 /></td>
<td><img src="./img/16.png" width=400></td>
</tr>
<tr>
<th>Fill Info - Fill in the relevant information for the target board.</th>
<th>Finish Install - After installation is complete, click "Finish" to exit.</th>
<th>System Interface - The Jetson Orin Nano system interface after installation is complete (Result presentation).</th>
</tr>
<tr>
<td><img src="./img/17.png" width=400 /></td>
<td><img src="./img/18.png" width=450 /></td>
<td><img src="./img/19.png" width=500 /></td>
</tr>
</table>
</div>

   - ### System environment initial setup Steps
      - Update the operating environment.
      ```bash
         sudo apt update
         sudo apt upgrade -y
      ```
     - Install required dependencies for pyenv Ubuntu
      ```bash
  
         sudo apt install update
         sudo apt install -y make build-essential libssl-dev zlib1g-dev \
            libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
            libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
      ```
     - Install nano
     ```bash
          sudo apt install nano
     ```
     - pyenv Installation
      ```bash
      curl https://pyenv.run | bash
      export PATH="$HOME/.pyenv/bin:$PATH"
      eval "$(pyenv init -)"
      eval "$(pyenv virtualenv-init -)"
      ```
     -  Python Installation
      ```bash      
      pyenv install 3.11.7
      pyenv global 3.11.7
      echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
      echo 'eval "$(pyenv init -)"' >> ~/.bashrc
      echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc  
      source ~/.bashrc

      ```

      - **BNO055** Driver Installation 
      ```bash
      sudo apt update
      sudo apt install i2c-tools -y
      sudo i2cdetect -y -r 7 
      python -m pip install --upgrade --user \
         adafruit-circuitpython-bno055 \
         circuitpython-bno055 \
         Jetson.GPIO \
         smbus2

      ```

      - **ASUS AC1200** or **TP Link AC1300** Driver Installation 
      ```bash
      mkdir -p ~/src && cd ~/src/
      git clone https://github.com/morrownr/88x2bu-20210702.git
      cd ~/src/88x2bu-20210702/
      sudo ./install-driver.sh

      sudo apt install dkms git -y && \
      sudo git clone https://github.com/RinCat/RTL88x2BU-Linux-Driver.git /usr/src/rtl88x2bu-git && \
      sudo sed -i 's/PACKAGE_VERSION="@PKGVER@"/PACKAGE_VERSION="git"/' /usr/src/rtl88x2bu-git/dkms.conf && \
      sudo dkms add -m rtl88x2bu -v git && \
      sudo dkms install -m rtl88x2bu -v git

      ```
      - __OpenCV Installation Instructions, please refer to Section [3-2 OpenCV Introduction](../OpenCV/README.md)__

      - Setting up Program Automatic Startup  Download __[Set_Auto_Run.sh](./code/Set_Auto_Run.sh)__ to run
      ```bash
      sudo bash ./Set_Auto_Run.sh
      ```

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 