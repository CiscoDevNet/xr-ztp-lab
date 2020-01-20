#!/usr/bin/env python

import sys
import tempfile
sys.path.append("/pkg/bin/")
from ztp_helper import ZtpHelpers

ztp=ZtpHelpers()

config = """!
hostname ${HOSTNAME}
service timestamps log datetime msec
service timestamps debug datetime msec
domain name virl.info
domain lookup disable
telnet vrf default ipv4 server max-servers 10
telnet vrf Mgmt-intf ipv4 server max-servers 10
username cisco
 group root-lr
 group cisco-support
 password 7 14141B180F0B
!
username admin
 group root-lr
 group cisco-support
 password 7 1218011A1B05
!
username lab
 group root-lr
 group cisco-support
 password 7 060A0E23
!
tpa
 vrf default
  address-family ipv4
   default-route mgmt
   update-source dataports MgmtEth0/RP0/CPU0/0
  !
  address-family ipv6
   default-route mgmt
   update-source dataports MgmtEth0/RP0/CPU0/0
  !
 !
!
line template vty
 timestamp
 exec-timeout 720 0
!
line console
 exec-timeout 0 0
!
line default
 exec-timeout 720 0
!
vty-pool default 0 50
call-home
 service active
 contact smart-licensing
 profile CiscoTAC-1
  active
  destination transport-method http
 !
!
control-plane
 management-plane
  inband
   interface all
    allow all
   !
  !
 !
!
interface Loopback0
 description Loopback
 ipv4 address 192.168.0.2 255.255.255.255
!
interface MgmtEth0/RP0/CPU0/0
 description OOB Management
 ipv4 address ${IP} 255.255.255.0
!
interface GigabitEthernet0/0/0/0
 description to unmanagedswitch-1
 ipv4 address 10.0.0.3 255.255.255.0
!
router static
 address-family ipv4 unicast
  0.0.0.0/0 198.18.1.1
 !
!
ssh server v2
end
"""

with tempfile.NamedTemporaryFile(delete=True) as f:
        f.write("%s" % config)
        f.flush()
        f.seek(0)
        print ztp.xrapply(f.name)


cmd = "curl -X POST http://198.18.134.50:8181/ztp/status/${SERIAL}/1"
process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process.communicate()