#!/usr/bin/env python

import os, sys
import pwd, grp
import time
import signal
import daemon, lockfile
from PilightReceiver import PilightReceiver
from HueSender import HueSender

class PilightHueBridge(object):

        stdin_path = "/dev/null"
        stdout_path = "/tmp/testdaemon.out"
        stderr_path =  "/tmp/testdaemon.err"
        pidfile_path =  "/var/run/pir-motion.pid"
        pidfile_timeout = 3
        terminate = False
        
        def __init__(self, debugMode = False):
            self.debugMode = debugMode
            self.pilightReceiver = PilightReceiver(self, 5)
            self.hue = HueSender(self)
            print('Initialized')
            
        def proxyUpdate(self, update):
            self.hue.processUpdate(update)
            self.pilightReceiver.processUpdate(update)

        def emit(self, message):
            print(message)

        def debug(self, message):
            if self.debugMode is True:
                self.emit(message)

        def run(self):
            self.emit('Daemon PID: %s' % os.getpid())
            self.pilightReceiver.start()
            self.hue.start()
            while True:
                if self.terminate:
                    self.emit('Terminated')
                    break
                
                time.sleep(2)    
                 
        def shutdown(self, a, b):
            self.emit('Catched SIGTERM')
            self.pilightReceiver.shutdown()
            self.hue.shutdown()
            self.terminate = True   

if __name__ == "__main__":
    
    bridge = PilightHueBridge()
    
    context = daemon.DaemonContext(
        working_directory='/tmp',
        umask=0x002,
        #pidfile=lockfile.FileLock(bridge.pidfile_path),
    )
        
    context.signal_map = {
        signal.SIGTERM: bridge.shutdown
    }    
    
    context.stdout = open(bridge.stdout_path, 'w+')
    context.stderr = open(bridge.stderr_path, 'w+', buffering=0)
    
    uid = pwd.getpwnam('nobody').pw_uid
    gid = grp.getgrnam('nogroup').gr_gid
    
    os.chown(bridge.stdout_path, uid, gid)
    os.chown(bridge.stderr_path, uid, gid)
    
    context.uid = uid;
    context.gid = gid;
    
    with context:
        bridge.run()