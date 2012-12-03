# UCLA - Fall 2012 - CS 131 Programming Languages
### Professor: Paul Eggert

## Project

See http://cs.ucla.edu/classes/fall12/cs131/hw/pr.html for prompt.

## Usage

Each server can be run individually with their associated `bash` scripts:

 * `run_blake`
 * `run_bryant`
 * `run_gasol`
 * `run_howard`
 * `run_metta`

All of the servers can be run as jobs using the `run_all_servers` `bash` script.

After the servers have been started, the network topology can be established with the `setup_relationships` `bash` script. This script acts as a sort of external party that tells the servers what their peers are. When a server A is made aware of a peer, server B, it attempts to connect with that peer so that peer, server B, will establish server A as its own peer. This is done by sending the `PEER` command via `telnet` (see `setup_relatoinships`).

An example of the commands that can be sent after relationship establishment can be found in the `test_servers` `bash` script. Running this script establishes a user location and then makes a request from each server to verify that the user data propagated through the servers appropriately.

## References

 * http://twistedmatrix.com/trac/
 * http://twistedmatrix.com/trac/wiki/Documentation
 * http://twistedmatrix.com/documents/current/core/howto/index.html
 * http://twistedmatrix.com/documents/current/api/classIndex.html
 * https://github.com/dustin/twitty-twister
