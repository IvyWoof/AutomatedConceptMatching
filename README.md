# AutomatedConceptMatching
AutomatedConceptMatching is a script that automates the comparison of concepts found in the MIMOSA Standard and ISO 10303-239 PLCS Standard. The script delivers the matches score, their description, name and relationships through the use of FuzzyWuzzy, to a database store. The database can be accessed through the provided web interface inside a virtual machine so that users can view, search and interact with the results. 

<h2>Initial Setup and Configuration</h2>

Import the supplied OVF file into either VMware Workstation/Player or VMware ESXi by following the procedure from VMware:
<br>VMware Workstation or Player
<br>https://docs.vmware.com/en/VMware-Workstation-Player-for-Windows/16.0/com.vmware.player.win.using.doc/GUID-DDCBE9C0-0EC9-4D09-8042-18436DA62F7A.html
<br>VMware ESXi
<br>https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.hostclient.doc/GUID-8ABDB2E1-DDBF-40E3-8ED6-DC857783E3E3.html

Configure VM network as per your local environment, either in Bridged mode or Nat for VMware Workstation; VMware ESXi configure VM Network to be on one with DHCP.

Open VM remote console, login with the following credentials:
<br>User: mimosa
<br>Passwprd: HELPplcs22

Run ifconfig to find the current IP Address.

SSH using same credentials.

Change directory to:
<br>/home/mimosa/AutomatedConceptMatching

Cat config.ini to view current Thresholds and Weighting. SQL Server Configuration shouldn't require changing.
<br>If Thresholds or Weighting need to be changed:
<br>VIM config.ini and make the required changes.
<br>mySQL Server credentials:
<br>user: matches
<br>password: HELP!plcs22


<h2>Setup Automated Matching Script</h1>
The automated matching script is contained in the main.py file. The program contains a config.ini file where you will need to add your SQL server information.
To generate this, please run the program once. You will then be able to populate the config.ini file with the following options.


[THRESHOLDANDWEIGHTING]

threshold = 40

name weighting = 65

description weighting = 23

relationship weighting = 12


[SQLSERVERCONFIG]

user = root

password = password1

database = automatedmatching


<h3>Threshold and Weighting</h3>

Please ensure you have entered a threshold between 0 and 100. This will determine what the minimum similarity score shown to you will be.

To determine the weighting of the name, description and relationship similarity values please enter a combination of numbers that total 100%.

It is important that the database you enter in the config.ini file is the same database you will be using to connect to the web interface.


<h2>Display Results of Matches</h2>
To run a new analysis, drop existing data from the database and repopulate,
<br>Run:
<br>python3 main.py
<br>
For CLI view of Concept Matches,
<br>Run:
<br>python3 show_matches.py

<br>For GUI view, browse to the IP address assigned via DHCP.
