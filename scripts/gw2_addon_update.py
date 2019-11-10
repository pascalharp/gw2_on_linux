#!/usr/bin/env python3

import hashlib
import requests
import os
import logging
import json
import tarfile
import io
import shutil

check_arcdps = False
check_d9vk = False

# path to dll install dir (without wine prefix!)
base = './drive_c/Program Files/Guild Wars 2/bin64/'

arcdps_path = 'https://www.deltaconnected.com/arcdps/x64/'
arcdps_checksum = 'd3d9.dll.md5sum'
arcdps_file = 'd3d9.dll'

d9vk_api = 'https://api.github.com/repos/Joshua-Ashton/d9vk/releases'
d9vk_version = 'd9vk_current.txt'
d9vk_file = 'd3d9_chainload.dll'
d9vk_file_src = '/x64/d3d9.dll'

def download_arcdps():
    if os.path.isfile(base+arcdps_file):
        logging.info("Backing up old file as "+arcdps_file+".backup")
        os.rename(base+arcdps_file,base+arcdps_file+'.backup')
    r = requests.get(arcdps_path + arcdps_file, allow_redirects=True, timeout=5)
    if not r.ok:
        logging.error("Failed to download "+arcdps_file+". Aborting")
        return
    with open(base+arcdps_file,'wb') as f:
        f.write(r.content)
    logging.info("arcdps updatet")


def update_arcdps():
    logging.info("Checking arcdps")
    if not os.path.isfile(base+arcdps_file):
        logging.info(arcdps_file + " does not exist yet")
        download_arcdps()
    else:
        r = requests.get(arcdps_path + arcdps_checksum, allow_redirects=True, timeout=5)
        if not r.ok:
            logging.error("Failed to download "+arcdps_checksum+". Aborting.")
            return
        md5_up = str(r.content,'ASCII').split(' ')[0]
        hash_md5 = hashlib.md5()
        with open(base+arcdps_file,'rb') as f:
            for c in iter(lambda: f.read(4096), b''):
                hash_md5.update(c)
        md5_local = hash_md5.hexdigest()
        if md5_up == md5_local:
            logging.info("md5 sums are matching, nothing to do")
        else:
            logging.info("md5 sums differ, updating...")
            download_arcdps()
    return

def download_d9vk(path):
    logging.info("Downloading d9vk")
    r = requests.get(path, allow_redirects=True, timeout=5)
    if not r.ok:
        logging.error("Failed downloading d9vk. Aborting")
        return False
    t = tarfile.open(mode='r:*',fileobj=io.BytesIO(r.content))
    d = t.getmembers()[0]
    if not d.isdir():
        logging.error("Failed reading tarfile. Aborting")
        return False
    t.extract(t.getmember(d.name+d9vk_file_src),path=base)
    if os.path.isfile(base+d9vk_file):
        logging.info("Backing up old file as "+d9vk_file+".backup")
        os.rename(base+d9vk_file,base+d9vk_file+'.backup')
    logging.info("Copying new file over")
    shutil.copy(base+d.name+d9vk_file_src,base+d9vk_file)
    return True


def write_d9vk_version(version):
    logging.info("Saving current d9vk version: "+version)
    with open(base+d9vk_version,'w') as f:
        f.write(version)
    return

def update_d9vk():
    logging.info("Checking d9vk")
    r = requests.get(d9vk_api, allow_redirects=True, timeout=5)
    if not r.ok:
        logging.error("Failed to connect to github. Aborting")
        return
    j = json.loads(r.content)
    latest = j[0].get('name')
    current = "Not yet initialized"
    if os.path.isfile(base+d9vk_version):
        with open(base+d9vk_version,'r') as f:
            current = f.read().strip('\n\r')
    else:
        logging.info("No d9vk version file found. Installing d9vk")
    if current == latest and current != "Not yet initialized":
        logging.info("d9vk is up to date, nothing to do")
    else:
        logging.info("d9vk is out of date, updating...")
        logging.info("Current: "+current)
        logging.info("Latest: "+latest)
        d9vk_download = j[0].get('assets')[0].get('browser_download_url')
        success = download_d9vk(d9vk_download)
        if success:
            write_d9vk_version(latest)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s | %(levelname)s: %(message)s',filename=base+'gw2_addon_update.log',level=logging.INFO)
    logging.info("Checking for updates")
    if os.getenv('GW2_UPDATE_ARCDPS','false') == 'true' or check_arcdps:
        update_arcdps()
    else:
        logging.info("Skipping arcdps")
    if os.getenv('GW2_UPDATE_D9VK','false') == 'true' or check_d9vk:
        update_d9vk()
    else:
        logging.info("Skipping d9vk")
    logging.info("Done")
    exit(0);

