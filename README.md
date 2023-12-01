# Pi|SWORD Install and Configuration
## Installing the operating system
- Install the latest version of Raspbian on your Raspberry Pi or Virtual Machine from the [Raspberry Pi Foundation Site](https://www.raspberrypi.org/downloads/raspbian/).
- Once the installation is complete, update the system by running the following commands:
```bash
sudo apt update -y
sudo apt upgrade -y
```
## Install Optional packages
- Install any additional desired packages by running the following command:
```bash
# Install optional packages
sudo apt-get install vim locate virtualenv -y

# Install Visual Studio Code (Optional)
sudo apt-get install code -y

# Install VMWare Tools (Optional, VMWare Only)
sudo mount /dev/cdrom
mkdir -p ~/Downloads/vmware-tools
cp -r /media/cdrom0/ ~/Downloads/vmware-tools
tar xvzf VMwareTools-*.tar.gz
cd vmware-tools-distrib
sudo apt-get install --no-install-recommends libglib2.0-0
sudo apt-get install --no-install-recommends build-essential
sudo apt-get install gcc-4.3 linux-headers-$(uname -r)
sudo ./vmware-install.pl 
```
If you get an error about not being able to run the configuration script, launch it manually by running the following command:
```bash
sudo /usr/bin/vmware-config-tools.pl
```

## Configure required services (Optional)
- Configure the SSH service by running the following command:
```bash
sudo vi /etc/ssh/sshd_config
# Uncomment the following lines:
PasswordAuthentication yes
PubkeyAuthentication yes
# Save and exit the file

# To enable the ssh server to start on boot, run the following command:
sudo systemctl enable --now ssh
```

## Install docker
- If you are using a Raspberry Pi, you will need to install docker manually by running the following commands:
```bash
# Uninstall old versions of docker
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done

# Raspberry Pi Install Only:
## Add Docker’s official GPG key (Raspberry Pi ):
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/raspbian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

## Setup Docker's Apt repository (Raspberry Pi Only):
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/raspbian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Virtualized Raspberry Pi OS Install Only:
## Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

## Add the repository to Apt sources:
### NOTE: If you receive an error about 'i386' during this step, use 'amd64' as the architecture
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update


# Install the latest Docker packages:
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Verify the installation:
sudo docker run hello-world

# Verify docker-compose is in path
which docker-compose
## If not, run the following command
sudo ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
```
References:
- [Docker Install Instructions - Virtualized Raspberry Pi](https://docs.docker.com/engine/install/debian/)
- [Docker Install Instructions - Raspberry Pi](https://docs.docker.com/engine/install/raspberry-pi-os/)

## Install MISP 
### TAU Docker MISP Install Instructions
- [Reference documentation](https://github.com/ostefano/docker-misp)
- Fetch install the latest version from their github page:
```bash
git clone https://github.com/ostefano/docker-misp.git
cd docker-misp
# Copy template.env to .env (on the root directory) and edit the environment variables at .env file
cp template.env .env
vi .env  # Change default passwords and other settings as desired
...
##
# Build-time variables
##

MISP_TAG=v2.4.177
MODULES_TAG=v2.4.176
PHP_VER=20190902
LIBFAUP_COMMIT=3a26d0a

PYPI_REDIS_VERSION="==5.0.*"
PYPI_LIEF_VERSION=">=0.13.1"
PYPI_PYDEEP2_VERSION="==0.5.*"
PYPI_PYTHON_MAGIC_VERSION="==0.4.*"
PYPI_MISP_LIB_STIX2_VERSION="==3.0.*"
PYPI_MAEC_VERSION="==4.1.*"
PYPI_MIXBOX_VERSION="==1.0.*"
PYPI_CYBOX_VERSION="==2.1.*"
PYPI_PYMISP_VERSION="==2.4.176"

# MISP_COMMIT takes precedence over MISP_TAG
# MISP_COMMIT=c56d537
# MODULES_COMMIT takes precedence over MODULES_TAG
# MODULES_COMMIT=de69ae3

##
# Run-time variables
##

# Email/username for user #1, defaults to MISP's default (admin@admin.test)
ADMIN_EMAIL=admin@pisword.local
# name of org #1, default to MISP's default (ORGNAME)
ADMIN_ORG=pisword
# defaults to an automatically generated one
ADMIN_KEY=
# defaults to MISP's default (admin)
ADMIN_PASSWORD=
# defaults to 'passphrase'
GPG_PASSPHRASE=
# defaults to 1 (the admin user)
CRON_USER_ID=
# defaults to 'https://localhost'
HOSTNAME=https://misp.pisword.local

# optional and used by the mail sub-system
SMARTHOST_ADDRESS=
SMARTHOST_PORT=
SMARTHOST_USER=
SMARTHOST_PASSWORD=
SMARTHOST_ALIASES=

# optional comma separated list of IDs of syncservers (e.g. SYNCSERVERS=1)
# For this to work ADMIN_KEY must be set, or AUTOGEN_ADMIN_KEY must be true (default)
SYNCSERVERS=
# note: if you have more than one syncserver, you need to update docker-compose.yml
SYNCSERVERS_1_URL=
SYNCSERVERS_1_NAME=
SYNCSERVERS_1_UUID=
SYNCSERVERS_1_KEY=

# These variables allows overriding some MISP email values.
# They all default to ADMIN_EMAIL.

# MISP.email, used for notifications. Also used
# for GnuPG.email and GPG autogeneration.
# MISP_EMAIL=

# MISP.contact, the e-mail address that
# MISP should include as a contact address
# for the instance's support team.
# MISP_CONTACT=

# Enable GPG autogeneration (default true)
# AUTOCONF_GPG=true

# Enable admin (user #1) API key autogeneration
# if ADMIN_KEY is not set above (default true)
# AUTOGEN_ADMIN_KEY=true

# Disable IPv6 completely (this setting will persist until the container is removed)
DISABLE_IPV6=true
```
- Build and run the containers
```bash
sudo docker-compose build
sudo docker-compose up
```

### MISP Docker Install Instructions
- Fetch and install the latest version of the MISP Docker repository by running the following command:
```bash
git clone https://github.com/MISP/misp-docker
cd misp-docker
# Copy template.env to .env (on the root directory) and edit the environment variables at .env file
cp template.env .env
vi .env  # Change default passwords and other settings as desired
...
MYSQL_HOST=misp_db
MYSQL_DATABASE=misp
MYSQL_USER=misp
MYSQL_PASSWORD=misp # rahvy1-dunwuj-Wezcum
MYSQL_ROOT_PASSWORD=misp # dyWfoq-totvon-5durqy

MISP_ADMIN_EMAIL=admin@admin.test # Change to admin@misp.pisword.local
MISP_ADMIN_PASSPHRASE=admin # Will update this later inside of application
MISP_BASEURL=https://localhost # Change to https://misp.pisword.local

POSTFIX_RELAY_HOST=relay.fqdn
TIMEZONE=Europe/Brussels # Change to America/New_York

DATA_DIR=./data
```
- Build the containers
```bash 
sudo docker-compose build
# OR
sudo docker-compose -f docker-compose.yml build
```
- Start the containers
```bash
sudo docker-compose up
# or
sudo docker-compose -f docker-compose.yml up
```

- Add the following line to your /etc/hosts file:
```bash
localhost misp.pisword.local
```

References:
- [MISP Docker Install Instructions](https://github.com/ostefano/docker-misp)
- [MISP Project Website](http://www.misp-project.org)

# Configure MISP
## Generate API KEY
- Login to MISP using the default credentials ('admin@pisword.local', 'admin')
- Change the admin password to something more secure
- Navigate to the [Auth Keys](https://misp.pisword.local/auth_keys/add) page
- Copy the API key to ~/pisword/config/misp.yaml for later use:
```bash
Pidev MISP API Key: fpO6PsSC4JlfYbI0SI0BwFE9KDjbknYb25VlZbDp 
PiSword MISP API Key: Nl1w8y1vSyFT5Kmqc2rb7xPmSewh3TzGXVAjd8yF
pisword-dev MISP API Key: qEpGART6KisGULUm60qOYE4nbi9uZN9v8v9kbtm5
```


# Test PyMISP Script
## Setup virtual environment
- Uninstall all versions of virtualenv and reinstall the latest version:
```bash
pip3 uninstall virtualenv
sudo pip3 uninstall virtualenv
sudo apt purge python3-virtualenv
sudo pip3 install virtualenv
```
- Next, create a new virtual environment
```bash
python -m venv venv
source venv/bin/activate

# If you get an error about python not being found, run the following:
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 2
sudo update-alternatives --config python

# If you get an error about ensurepip not being available, run the following:
sudo apt-get install python3-venv
```

## Install PyMISP
```bash
# Install rust (dependency)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs/ | sh
source $HOME/.cargo/env
# x86 only: sudo apt get install g++-multilib libc6-dev-i386 gcc-multilib -y
sudo apt-get install libffi-dev libssl-dev python3-dev build-essential libjpeg62-turbo-dev zlib1g-dev cmake libfuzzy-dev ninja-build cargo pkg-config python3-tk
pip install --upgrade setuptools wheel pip

# Compile and install lief x86 (pymisp dependency)
git clone https://github.com/lief-project/LIEF.git
cd LIEF
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DLIEF_PYTHON_API=on -DPYTHON_EXECUTABLE=$(which python3) -DPYTHON_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))') -GNinja ..
make
cd apt/python
python3 stepup.py bdist_wheel
pip install dist/lief*.whl 

# Compile and install cryptography (pymisp dependency)
git clone https://github.com/pyca/cryptography.git && cd cryptography


# Install PyMISP Package
pip install pymisp[virustotal,openioc,fileobjects,docs,pdfexport,email]
# OR
git clone https://github.com/MISP/PyMISP.git && cd PyMISP
git submodule update --init

# Install pytest dependencies

pip install poetry pipenv pytest pytest-cov pydeep2 zipp 
poetry install -E fileobjects -E openioc -E virustotal -E docs -E pdfexport -E email
```

## Test PyMISP


```python
import json
from pymisp import ExpandedPyMISP as PyMISP
MISP_URL='https://misp.pisword-dev.local'
MISP_API_KEY='qEpGART6KisGULUm60qOYE4nbi9uZN9v8v9kbtm5'
ssl = verifycert = False
misp = PyMISP(MISP_URL, MISP_API_KEY, ssl, verifycert)
# load default feeds
misp.load_default_feeds()
feeds = misp.feeds()
# Print all feed names
>>> for feed_index, feed in enumerate(feeds):
...     print(f"{feed_index}:\t {feed['Feed']['name']}")
...
0:       CIRCL OSINT Feed
1:       The Botvrij.eu Data
2:       ELLIO: IP Feed (Community version)
3:       blockrules of rules.emergingthreats.net
4:       Tor exit nodes
5:       Tor ALL nodes
6:       cybercrime-tracker.net - all
7:       Phishtank online valid phishing
8:       ip-block-list - snort.org
9:       diamondfox_panels
10:      pop3gropers
11:      Feodo IP Blocklist
12:      OpenPhish url list
13:      firehol_level1
14:      IPs from High-Confidence DGA-Based C&Cs Actively Resolving - requires a valid license
15:      Domains from High-Confidence DGA-based C&C Domains Actively Resolving
16:      ci-badguys.txt
17:      alienvault reputation generic
18:      blocklist.de/lists/all.txt
19:      VNC RFB
20:      sshpwauth.txt
21:      sipregistration
22:      sipquery
23:      sipinvitation
24:      DNS recursion desired
25:      DNS recursion desired IN ANY
26:      DNS CH TXT version.bind
27:      IP protocol 41
28:      SMTP data
29:      SMTP greet
30:      TELNET login
31:      All current domains belonging to known malicious DGAs
32:      VXvault - URL List
33:      abuse.ch SSL IPBL
34:      http://cybercrime-tracker.net hashlist
35:      http://cybercrime-tracker.net gatelist
36:      blocklist.greensnow.co
37:      This list contains all domains - A list for administrators to prevent mining in networks
38:      This list contains all optional domains - An additional list for administrators
39:      This list contains all browser mining domains - A list to prevent browser mining only
40:      URLHaus Malware URLs
41:      CyberCure - IP Feed
42:      CyberCure - Blocked URL Feed
43:      CyberCure - Hash Feed
44:      ipspamlist
45:      mirai.security.gives
46:      malsilo.url
47:      malsilo.ipv4
48:      malsilo.domain
49:      malshare.com - current all
50:      Panels Tracker
51:      IPsum (aggregation of all feeds) - level 1 - lot of false positives
52:      IPsum (aggregation of all feeds) - level 2 - medium false positives
53:      IPsum (aggregation of all feeds) - level 3 - low false positives
54:      IPsum (aggregation of all feeds) - level 4 - very low false positives
55:      IPsum (aggregation of all feeds) - level 5 - ultra false positives
56:      IPsum (aggregation of all feeds) - level 6 - no false positives
57:      IPsum (aggregation of all feeds) - level 7 - no false positives
58:      IPsum (aggregation of all feeds) - level 8 - no false positives
59:      DigitalSide Threat-Intel OSINT Feed
60:      Metasploit exploits with CVE assigned
61:      Malware Bazaar
62:      PhishScore
63:      Threatfox
64:      MalwareBazaar
65:      URLhaus
66:      URL Seen in honeypots
67:      SSH Bruteforce IPs
68:      Telnet Bruteforce IPs
69:      threatfox indicators of compromise
70:      James Brine Bruteforce IPs

# Prettify the response
firehol = feeds[13]['Feed']
pretty_data = json.dumps(firehol, indent=4)
print(pretty_data)
{
    "id": "14",
    "name": "firehol_level1",
    "provider": "iplists.firehol.org",
    "url": "https://raw.githubusercontent.com/ktsaou/blocklist-ipsets/master/firehol_level1.netset",
    "rules": "{\"tags\":{\"OR\":[],\"NOT\":[]},\"orgs\":{\"OR\":[],\"NOT\":[]}}",
    "enabled": false,
    "distribution": "0",
    "sharing_group_id": "0",
    "tag_id": "6",
    "default": true,
    "source_format": "freetext",
    "fixed_event": true,
    "delta_merge": true,
    "event_id": "0",
    "publish": false,
    "override_ids": false,
    "settings": "{\"csv\":{\"value\":\"\",\"delimiter\":\",\"},\"common\":{\"excluderegex\":\"\"}}",
    "input_source": "network",
    "delete_local_file": false,
    "lookup_visible": true,
    "headers": null,
    "caching_enabled": false,
    "force_to_ids": false,
    "orgc_id": "0",
    "cache_timestamp": false
}

```

## Install pisword
- Initialize virtual environment
```bash
source venv/bin/activate
```
- Install dependencies
```bash
pip install -r requirements.txt
# OR
pip install flask flask_restful pymisp pyyaml pyflowchart requests cssselect lxml importlib curses pyautogui
```
### Enable SSL configuration
- Generate a self-signed SSL certificate
```bash
openssl req -x509 -newkey rsa:2048 -keyout ~/Documents/pisword/certs/client.key -out ~/Documents/pisword/certs/client.crt -days 3650 -nodes
```
- Ensure that the path to the MISP SSL cert is exported for SSL verification
```bash
# export REQUESTS_CA_BUNDLE=~/Documents/docker-misp/ssl/cert.pem
export REQUESTS_CA_BUNDLE=~/Documents/pisword/certs/client.crt

# MISP Keys are stored at the following location:
/etc/nginx/ssl/misp.key
```


```


### References:
- [PyMISP GitHub Page](https://github.com/MISP/PyMISP)


# Setup GNS3 For testing 
- Reference: [GNS3 Windows Install](https://docs.gns3.com/docs/getting-started/installation/windows/)
1. Download the latest version of GNS3 from the [GNS3 Website](https://www.gns3.com/software/download)
2. Follow the instructions and install using default settings
3. Download the GNS3 VM for VMWare Workstation using this [link](https://github.com/GNS3/gns3-gui/releases/download/v2.2.43/GNS3.VM.VMware.Workstation.2.2.43.zip)
4. Unzip the downloaded zip archive
```bash
unzip ~/Downloads/GNS3.VM.VMware.Workstation.2.2.43.zip
```
5. Import `GNS3 VM.ova` into VMWare Workstation by clicking `File > Open...` and selecting the `GNS3 VM.ova` file
6. In the GNS3 Setup Wizard, select `Vmware (recommended)` under Virtualization Software, and select the GNS3 VM from the drop down menu. 
7. Configure the following network settings:
    - Adapter 1: Host-Only (VMNet1 - Where GNS3 will get its IP address via DHCP)
    - Adapter 1: Bridged (vmnet0) - Ethernet Interface (Where pfSense will get its IP address via DHCP)
    - Adapter 2: Host-Only (VMNet2 - Where PiSword will get its IP address via DHCP from DHCP)
7. Take a snapshot once the VM is up and running
8. Access the Web-UI via http://192.168.220.128
- Alnatively, can login using ssh
```bash
ssh gns3@192.168.220.128
```
10. Click `New Template` -> `Install appliance from server` -> `Search by name` -> `pfSense` -> `Download this appliance` or `Import` if already downloaded
11. Under `pfSense version 2.7.0` import or download the qcow2 image using the provided [link](https://sourceforge.net/projects/gns-3/files/Empty%20Qemu%20disk/empty100G.qcow2/download)
12. Open the virtual machine network configuration editor and create two new host-only networks (vmnet2 and vmnet3)
  - vmnet0: 192.168.XX.0/24 (Depends on local DHCP settings)
  - vmnet2: 10.0.50.0/24 (PiSword Network)
13. Drag the pfSense template into the network topology and configure the network adapters as follows:
  - Set Adapter 0: vmnet0
  - Set Adapter 1: vmnet2
14. Default pfSense credentials are `admin`:`pfsense`

# Setup pfSense Firewall (Testing)
1. Download the latest ISO image from the [pfSense website](https://www.pfsense.org/download/)
2. Extract the ISO from the archive:
```bash
gunzip pfSense-CE-2.7.0-RELEASE-amd64.iso.gz
```
3. Verify the file hash:
```bash
sha256sum pfSense-CE-2.7.0-RELEASE-amd64.iso
```
4. Create a new virtual machine with the following settings:
    - 2GB RAM
    - 2 CPU Cores
    - 2 Network Adapters
        - Adapter 1: NAT
        - Adapter 2: Host-Only
    - 20GB HDD
5. Install the pfSense ISO on the virtual machine
6. Configure the WAN interface to use DHCP

# Install and configure pfSense API
- Reference: [pfSense API Documentation](https://github.com/jaredhendrickson13/pfsense-api)
1. Log into the pfSense console in GNS3 and select `8` to open a shell
2. Install the pfSense API package by running the following command:
```bash
/bin/sh
pkg -C /dev/null add https://github.com/jaredhendrickson13/pfsense-api/releases/latest/download/pfSense-2.7-pkg-API.pkg && /etc/rc.restart_webgui
```
3. SSL Integration and Certificate Verification
    - Make a new CA in the PFSense GUI menu 
    - System > Cert Manager > CAs > Add
    - Store the certificate in the `./certs` folder
    - Add the CA to the trusted CA store on the PiSword host
    ```bash
    # Install ca-certificates if it is not already installed:
    sudo apt-get install ca-certificates curl gnupg -y
    # Copy the CA certificate to the trusted CA store
    sudo cp ./certs/CA.crt /usr/local/share/ca-certificates/pfsense_ca.crt
    # Update the trusted CA store
    sudo update-ca-certificates
    ```
4. Issue a new certificate for the PfSense Server
    - System > Cert Manager > Certificates > Add/Sign
    - Create a new server certificates and name it `pfsense_server`
    - Go to System > Advanced > Admin Access
    - Set the SSL certificate to `pfsense_server`
    - Save
5. Issue a new certificate for MISP 
    - System > Cert Manager > Certificates > Add/Sign
    - Create a new server certificates and name it `misp_server`
    - Go to System > Advanced > Admin Access
    - Set the SSL certificate to `misp_server`
    - Save them in the ./certs folder
    - Copy the new certificates to the `docker-misp` folder
    ```bash
    # Backup the old certificates
    cp ~/Documents/docker-misp/ssl/cert.pem ~/Documents/docker-misp/ssl/cert.pem.bak
    cp ~/Documents/docker-misp/ssl/key.pem ~/Documents/docker-misp/ssl/key.pem.bak
    cp ~/Documents/docker-misp/ssl/dhparams.pem ~/Documents/docker-misp/ssl/dhparams.pem.bak
    # Copy the new certificates
    cp ./certs/misp_server.crt ~/Documents/docker-misp/ssl/cert.pem
    cp ./certs/misp_server.key ~/Documents/docker-misp/ssl/key.pem
    # Generate a new dhparams file 
    openssl dhparam -out ~/Documents/docker-misp/ssl/dhparams.pem 2048
    ```

5. (Optional) Import Certificates into Firefox
    - Go to `Preferences > Privacy & Security > View Certificates > Authorities > Import`
    - Select the `CA.crt` file from the `./certs` folder
    - Check the `Trust this CA to identify websites` box
    - Click `OK`

## Create an API user     
1. Create API Users group
    - System > User Manager > Groups > Add
    - Group Name: `api_users`
    - Description: `API Users`
    - Effective Privileges:
        Name: `API - Services: Service Watchdog`
        Name: `WebCfg - System: API package`
        Name: `WebCfg - All pages`
2. Create API User
    - System > User Manager > Users > Add
    - Username: `pisword`
    - Password: `kn4%*iGbwbr}X4L`
    - Full Name: `API User`
    - Groups: `api_users`
    - Create Certificate for User
        - Descriptive Name: `API User Certificate`
        - Certificate Authority: `GNS3 CA`
        - Key type: `RSA`
        - Key Length: `2048`
        - Digest Algorithm: `SHA256`
        - Lifetime: `3650`
3. Copy down API key
    - System > User Manager > Users > pisword > API Keys
    - Copy down the client-id and API key
    - Example:
        - Username: `admin`
        - clientid: `61646db696e` 
        - api-key:`32b452f960c32b9c79215c55fc827b9f`
    - Example:
        - Usernane: `pisword`
        - clientid: `706973776f7264`
        - api-key: `9347b0f659c37d4c49554faa09b6a18c`
4. Set API key variable in the bashrc file on the PiSword host
```bash
echo "export PFSENSE_API_KEY='706973776f7264 9347b0f659c37d4c49554faa09b6a17c'" >> ~/.bashrc
```
5. Update the `./config/pfsense.yaml` file with the API key
## Create certificates for MISP, PiSword, and api-user
1. Following the same process as the pfSense server certificate, create a new certificate for the MISP server
    - System > Cert Manager > Certificates > Add/Sign
    - Create a new server certificates and name it `misp_server`
    - Go to System > Advanced > Admin Access
    - Set the SSL certificate to `misp_server`
    - Set the common name as `misp.pisword-dev.local`
    - Set an alternate common name as `misp.pisword.local`
    - Save the certificates to the `./certs` folder
2. Following the same process as the pfSense server certificate, create a new certificate for the PiSword server
    - System > Cert Manager > Certificates > Add/Sign
    - Create a new server certificates and name it `pisword_server`
    - Go to System > Advanced > Admin Access
    - Set the SSL certificate to `pisword_server`
    - Set the common name as `pisword.pisword-dev.local`
    - Set an alternate common name as `pisword.pisword.local`
    - Save the certificates to the `./certs` folder



```bash
- Stopping the docker container:
```bash
sudo docker stop be1c8900d861 69aee259ad7e ca0e35395a6b 26ce2f2da59b 067bb27c7f59
be1c8900d861
```
- Example PFSense Firewall Logs:
```bash
"Nov  7 05:55:08 pfSense filterlog[50918]: 4,,,1000000103,vmx0,match,block,in,4,0x0,,64,43867,0,DF,17,udp,32,192.168.33.1,255.255.255.255,51233,10001,12",
    "Nov  7 05:55:12 pfSense filterlog[50918]: 4,,,1000000103,vmx0,match,block,in,4,0x0,,64,44031,0,DF,17,udp,32,192.168.33.1,255.255.255.255,53278,10001,12",
    "Nov  7 05:55:18 pfSense filterlog[50918]: 4,,,1000000103,vmx0,match,block,in,4,0x0,,64,44109,0,DF,17,udp,32,192.168.33.1,255.255.255.255,51233,10001,12",
    "Nov  7 05:55:22 pfSense filterlog[50918]: 4,,,1000000103,vmx0,match,block,in,4,0x0,,64,44364,0,DF,17,udp,32,192.168.33.1,255.255.255.255,53278,10001,12"

# Fields 

```
- Example PFSense DHCP Logs:
```bash
Oct 20 17:20:26 pfSense dhcp6c[612]: Sending Solicit
Oct 20 17:20:26 pfSense dhcp6c[612]: transmit failed: Network is down
Oct 20 17:20:30 pfSense dhcp6c[612]: Sending Solicit
Oct 20 17:20:30 pfSense dhcp6c[612]: transmit failed: Network is down
Oct 20 17:20:37 pfSense dhcp6c[612]: exiting
Oct 20 17:20:38 pfSense dhcp6c[9189]: failed to open /usr/local/etc/dhcp6cctlkey: No such file or directory
Oct 20 17:20:38 pfSense dhcp6c[9189]: failed initialize control message authentication
Oct 20 17:20:38 pfSense dhcp6c[9189]: skip opening control port
Oct 20 17:20:39 pfSense dhcp6c[9396]: Sending Solicit
Oct 20 17:20:39 pfSense dhcp6c[9396]: transmit failed: Network is down
```
- Example PfSense System Logs:
```bash
Oct 20 17:20:26 pfSense dhcp6c[612]: Sending Solicit
Oct 20 17:20:26 pfSense dhcp6c[612]: transmit failed: Network is down
Oct 20 17:20:30 pfSense dhcp6c[612]: Sending Solicit
Oct 20 17:20:30 pfSense dhcp6c[612]: transmit failed: Network is down
Oct 20 17:20:37 pfSense dhcp6c[612]: exiting
Oct 20 17:20:38 pfSense dhcp6c[9189]: failed to open /usr/local/etc/dhcp6cctlkey: No such file or directory
Oct 20 17:20:38 pfSense dhcp6c[9189]: failed initialize control message authentication
Oct 20 17:20:38 pfSense dhcp6c[9189]: skip opening control port
Oct 20 17:20:39 pfSense dhcp6c[9396]: Sending Solicit
Oct 20 17:20:39 pfSense dhcp6c[9396]: transmit failed: Network is down
```
- Example PfSense Config History Logs:
```bash
{'time': 1699318469, 'description': 'admin@192.168.33.129 (Local Database): Successfully edited user pisword', 'version': '22.9', 'filesize': 52353}
{'time': 1699318430, 'description': 'admin@192.168.33.129 (Local Database): Created internal certificate pisword_api_user', 'version': '22.9', 'filesize': 52341}
{'time': 1699317752, 'description': 'admin@10.0.50.50 (Local Database): Updated Certificate Authority GNS3-CA', 'version': '22.9', 'filesize': 47762}
{'time': 1699317681, 'description': 'admin@192.168.33.129 (Local Database): Deleted certificate pisword_ovpn', 'version': '22.9', 'filesize': 47765}
{'time': 1699317629, 'description': 'admin@192.168.33.129 (Local Database): Updated Certificate Authority GNS3-CA', 'version': '22.9', 'filesize': 52431}
{'time': 1699286114, 'description': 'admin@192.168.33.129 (Local Database): Created internal certificate pfsense_client', 'version': '22.9', 'filesize': 52340}
{'time': 1699026820, 'description': '(system): wan IP configuration from console menu', 'version': '22.9', 'filesize': 47674}
{'time': 1698856751, 'description': 'admin@192.168.33.129 (Local Database): Firewall: NAT: Port Forward - saved/edited a port forward rule.', 'version': '22.9', 'filesize': 47636}
{'time': 1698856742, 'description': 'admin@192.168.33.129 (Local Database): Firewall: NAT: Port Forward - saved/edited a port forward rule.', 'version': '22.9', 'filesize': 47634}
{'time': 1698855693, 'description': 'admin@192.168.33.129 (Local Database): DHCP Server settings saved', 'version': '22.9', 'filesize': 47595}
```

# Menu Examples
- Example Menu
```python
class Menu:
    """This class is used to manage the menu system."""
    pass

    def draw_menu(self, stdscr, header, options):
      pass

    def draw_form(self, stdscr, form_fields, form_responses=None, header=None):
      pass

    def draw_input_prompt(self, stdscr, prompt, header=None):
      """
      Draws an input prompt where the user can type a response.

      :param stdscr: The standard screen object from curses.
      :param prompt: The prompt to display to the user.
      :param header: An optional header to display above the prompt.
      """
      pass

    def run(self, stdscr):
        self.display_menu(stdscr)

    def display_menu(self, stdscr):
        while True:
            self.current_menu(stdscr)
            if not self.menu_stack:
                break
            self.current_menu = self.menu_stack.pop()
    def main_menu(self, stdscr):
        """
            Main menu implementation

            Should render like this:
            {self.top_header}
            SELECT AN OPTION:
            >>> 1. VIEW PLAYBOOKS
                2. CREATE PLAYBOOK
                3. EDIT PLAYBOOK
                4. LAUNCH PLAYBOOK
                5. STOP PLAYBOOK
                6. REMOVE PLAYBOOK
                7. CONFIGURE
                8. EXIT
        """                                                  
        pass

    def add_playbook_menu(self, stdscr):
        """ 
        Initial menu to create a new playbook 

        Should render like this:
        {self.playbook_header}

        NAME YOUR PLAYBOOK>>>  <user input>

        """
        pass

    def select_playbook_menu(self, stdscr, header):
        """
        Menu to select a playbook to edit or launch
        
        The menu should render like this:
        {header}

        SELECT A PLAYBOOK:
        >>> 1. PLAYBOOK1
            2. PLAYBOOK2
            ...
            N. BACK
        
        It should get the name of the header, and then return it to the calling function.
        """
    def draw_main_playbook_menu(self, stdscr, options, current_option, playbook, integration=None, logic=None):
        '''
        Renders the main playbook menu based on the provided options

                Should render like this:    
            {self.playbook_header}
            PLAYBOOK>>> <playbook name>
                TOOLBOX>>> <list of integrations>
                    BATTLE RHYTHM>>> (CONFIG) 
                        <playbook logic> or blank if no logic has been added yet
            
            SELECT AN OPTION:
            >>> 1. VIEW LOGIC # If no logic has been added yet, does not show this option
                2. ADD AN ACTION # If no logic has been added yet, this is the only option
                3. REMOVE AN ACTION # If no functions are in the playbook, does not show this option
                4. MODIFY AN ACTION # If no functions are in the playbook, does not show this option, but leads to trigger menu if there if only one function
                5. BACK # Returns to previous menu
        
        '''
        pass

      def edit_function_menu(self, stdscr, playbook, action='add'):
        """
        Menu for adding a function to a playbook

        It should render like this:
            # Submenu for adding a function to a playbook
            {self.playbook_header}
            PLAYBOOK>>> {playbook.name}
                TOOLBOX>>> {','.joint(self.config_mgr.integrations_list)}
                    BATTLE RHYTHM>>> (CONFIG) # Render logic that has been built so far
                        {self.playbook_mgr.render_playbook_logic(playbook)} 

            SELECT A TOOL:
            >>> 1. INTEGRATION1 
                2. INTEGRATION2
                ...
                N. BACK # {len(self.config_mgr.integrations_list) + 1}

            
            # Should pass the integrations_name and initialize it as a PlaybookFunction object
        """
        pass

        def integration_function_menu(self, stdscr, playbook, integration_name):
            """
            Menu for adding a function to a playbook

            It should render like this:
                {self.playbook_header}
                PLAYBOOK>>> {playbook.name}
                    TOOLBOX>>> 
                        TOOL>>> {integration_name}
                            BATTLE RHYTHM>>> (CONFIG) # Render logic that has been built so far
                                {self.playbook_mgr.render_playbook_logic(playbook)} 
                        
                SELECT AN ACTION:
                >>> 1. FUNCTION1
                    2. FUNCTION2
                    ...
                    N. BACK
            # Should pass the integrations name when it calls the add_trigger_menu method
            """
            pass

        def edit_trigger_menu(self, stdscr, playbook, integration_name):
          """
          Add or remove a function trigger (Called from the add_function_menu method)
              # Submenu after selecting a function or to add or remove a function trigger  
              {self.playbook_header}
              PLAYBOOK>>> {playbook.name.uppper()}
                  TOOLBOX>>> 
                      TOOL>>> {integration_name.upper()}
                          BATTLERHYTHM>>> (CONFIG) 
                              FUNCTION1:  >>>> # Will show triggers if any have been set
                                  <trigger_type_1: trigger_value_1 # Will only show multiple triggers if using a CONDITION trigger (omit if CONTINUOUS triggers not supported)
                                  <trigger_type_2: trigger_value_2>>>> # Same as above

              SELECT A TRIGGER:
                  1. CONTINUOUS  # Sets the 'always' parameter in the function trigger field, and returns to top playbook editor menu
                  2. TIME INTERVAL
                  3. CONDITION   # This is a placeholder for now, will be implemented later (give invalid option and remain on this menu for now)
                  4. BACK # Returns to previous menu and does not update the function trigger
              
              # Submenu for setting a function time inverval trigger value
              {self.playbook_header}
              PLAYBOOK>>> {playbook.name}
                  TOOL>>> {<integration name>}
                      BATTLERHYTHM>>> <function1> # Will show more if more functions have been configured


              SELECT A TIME INTERVAL (IN SECONDS, DEFAULT IS 60)>>> <user input> 
          """
          pass

        def exit_playbook_menu(self, stdscr, playbook, integration_name):
          """
          Menu asking the user if they want to save their playbook 

          Should render like this:
          {self.playbook_header}
          PLAYBOOK>>> {playbook.name}
              TOOLBOX>>>
                  TOOL>>> {integration_name}
                      BATTLE RHYTHM>>> (CONFIG) # Render logic that has been built so far
                          {self.playbook_mgr.render_playbook_logic(playbook)}

          WARNING: Confirming this action will overwrite the existing playbook file.
          
          SAVE PLAYBOOK:
          >>> 1. YES
              2. NO

          # If YES, save all of the playbook data in memory, write it to the file, and return to the main menu
          """
          pass

        def edit_on_success_menu(self, stdscr, playbook, integration_name):
          """
          Menu for adding or removing an on_success trigger

          It should render like this:
                  {self.playbook_header}
                  PLAYBOOK>>> {playbook.name}
                      TOOLBOX>>> 
                          TOOL>>> {integration_name}
                              BATTLE RHYTHM>>> (CONFIG) # Render logic that has been built so far
                                  {self.playbook_mgr.render_playbook_logic(playbook)} 
                          
                  IF THE ACTION SUCCEEDS, WHAT SHOULD HAPPEN NEXT?:
                  >>> 1. HALT PLAYBOOK
                      2. EXECUTE NEXT ACTION
                      N. BACK
          """
          pass

        def exit_playbook_menu(self, stdscr, playbook, integration_name):
          """Menu asking the user if they want to save their playbook"""
          pass

        def get_user_input_for_time_interval(self, stdscr):
          """Gets the user input for a time interval trigger."""  
          pass

        def launch_playbook_menu(self, stdscr):
          pass

        def stop_playbook_menu(self, stdscr):
          pass

        def remove_playbook_menu(self, stdscr):
          pass

        def configuration_menu(self, stdscr):
          """
          Menu for editing integration configurations

              Should look like this:
              # <self.header> stays at the top of the menu
              # Toolbox header will update with an *right after a new configuration is added
              TOOLBOX>>> MISP, INTEGRATION2, INTEGRATION3 
          
              SELECT AN OPTION:
              >>> 1. ADD INTEGRATION
                  2. REMOVE INTEGRATION
                  3. UPDATE INTEGRATION
                  4. RETURN TO MAIN MENU # Returns to main menu
          """
          pass

        def add_integration(self, stdscr, top_header_config):
          """
          # Submenu for adding or removing an integration
          {top_header}
          TOOLBOX>>> (CONFIG)
          
          WARNING: Modifying the configuration file only makes changes to the integration in memory.
          WARNING: You must the configuration file in the <self.integration_mgr.CONFIG_PATH> directory 
          in order to make these changes permanent.

          SELECT A TOOL:
          >>> 1. INTEGRATION1
              2. INTEGRATION2
              ...
              N. BACK
          
          
          # Submenu for adding an integration (Only allowed for integrations that are not already enabled, otherwise displays a message that all integrations are enabled)
          {top_header}
          TOOLBOX>>> (CONFIG)

          SELECT A TOOL:
          >>> 1. INTEGRATION1 # After adding, notify the user what feeds and playbook functions have been enabled and return to top of configuration menu
          """
          pass

        def update_integration(self, stdscr, top_header):
        """
               # Submenu for updating an integration
            # Header stays at the top of the menu
            TOOLBOX>>> (CONFIG)
                TOOL>>> <integration name>

            WARNING: Modifying the configuration file only makes changes to the integration in memory.
            WARNING: You must the configuration file in the <self.integration_mgr.CONFIG_PATH> directory 
            in order to make these changes permanent.
                
            SELECT AN OPTION: # This menu only provides fields that are in the integration's config file
            >>> 1. UPDATE API KEY # will modify the integration.api_key value
                2. UPDATE URL   # will modify the integration.url value
                3. UPDATE SSL   # will toggle the integration.ssl value
                4. UPDATE CERTIFICATE VERIFICATION # # will toggle the integration.verifycert value
                5. BACK # Returns to top of configuration menu
            
            # Submenu after selecting an option:
            # Header stays at the top of the menu
            TOOLBOX>>> (CONFIG)
                TOOL>>> <integration name>
            
            ENTER NEW <option_name>>>> <user input> # Ensure that you do not allow empty values or invalid values

            # Submenu after updating an integration
            # Header stays at the top of the menu
            TOOLBOX>>> (CONFIG)
                TOOL>>> <integration name>
            
            WARNING: MODIFYING INTEGRATION VALUES MAY CAUSE THE INTEGRATION TO STOP WORKING. 
            
            ARE YOU SURE YOU WANT TO PROCEED?

            SELECT AN OPTION:
            >>> 1. CANCEL # Returns to top of configuration menu
                2. PROCEED WITH UPDATE  # updates the values in memory, reloads integration, and returns to top of configuration menu (does not save to file)
        """
        pass

      def remove_integration(self, stdscr, top_header):
        """
        {top_header} # Stays at the top of the menu as the user selects an integration to remove
        TOOLBOX>>> (CONFIG)
        
        WARNING: Modifying the configuration file only makes changes to the integration in memory.
        WARNING: You must the configuration file in the <self.integration_mgr.CONFIG_PATH> directory 
        in order to make these changes permanent.

        SELECT A TOOL:
        >>> 1. INTEGRATION1
            2. INTEGRATION2
            ...
            N. BACK
        
        # Submenu after selecting an integration to remove
        {top_header}
        TOOLBOX>>> (CONFIG)
            TOOL>>> <integration name>

        WARNING: # Display warning message from IntegrationManager._generate_removal_warning()

        SELECT AN OPTION:
        >>> 1. CANCEL
            2. PROCEED WITH REMOVAL # Sets the integrations enabled status to false and reloads the configuration
        
        # Returns to main configuration menu
        """
        pass

```

- PiSword Unittest
```python
import unittest

def pretty(data):
    print(json.dumps(data.to_json(), indent=4))

import json; from classes import ConfigurationManager; config = ConfigurationManager(); misp = config.initialize_misp(); pfsense = config.integration_mgr.initialize_integration('pfsense'); 
print(pfsense.to_pretty(misp.enabled_feeds))
print(misp.get_event_data_by_type('ip-dst'))
print(pfsense.to_pretty(pfsense.rules))
print(pfsense.to_pretty(pfsense.get_logs('firewall')[0:5]))
print(pfsense.to_pretty(pfsense.interfaces))
print(pfsense.to_pretty(pfsense.rules[0].rule_data))

```

# Testing playbook creation
```python
from classes import ConfigurationManager, Playbook, PlaybookFunction; config = ConfigurationManager(); playbook = Playbook('test');
def check(playbook=playbook):
    print(f"playbook.name: {playbook.name}")
    print(f"playbook.filename: {playbook.filename}")
    print(f"playbook.path: {playbook.path}")
    print(f"playbook.functions: {playbook.functions}")
    print(f"playbook.integration_deps: {playbook.integration_deps}")
    print(f"playbook.logic: {playbook.logic}")
    print(f"playbook.data: {playbook.data}")
    print(f"playbook.enabled: {playbook.enabled}")
    print(f"playbook.exists: {playbook.exists}")
    print(f"playbook.is_running: {playbook.is_running}")

```

# Testing menu system
```python
import json; from classes import ConfigurationManager, PlaybookFunction; config = ConfigurationManager(); misp = config.initialize_misp(); pfsense = config.integration_mgr.initialize_integration('pfsense'); 
current_function_name = 'get_misp_event_by_type'
data_deps = config.get_data_dependencies_by_function(current_function_name)
options = data_deps.copy()
options.insert(0, "None") # prepend "None" to list
options.append("Back") # append "BACK" options to list
current_function = PlaybookFunction('get_misp_event_by_type')
selected_option = 1
if current_function.data_dependencies is None:
    current_function.data_dependencies = []

current_function.data_dependencies.append(options[selected_option])
functions = list(config.enabled_playbook_functions.keys())
```