/*
   Copyright (C) 2003-2011 Institute for Systems Biology
                           Seattle, Washington, USA.

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2.1 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

*/
package main

import (
	"os"
	"os/exec"
	"time"
)

// restarts process using the original commands after wait time in nanoseconds, then die
func RestartIn(waitn int64) {
	logger.Printf("RestartIn(%v secs)", waitn)
	time.Sleep(time.Duration(waitn)*time.Second)
	logger.Printf("RestartIn(): restarting")

	cmd, err := exec.LookPath(os.Args[0])
	if err != nil {
		logger.Printf("RestartIn(): exec %s", os.Args)
		logger.Warn(err)
		return
	}

	f := []*os.File{os.Stdin, os.Stdout, os.Stderr}
	_, err = os.StartProcess(cmd, os.Args, &os.ProcAttr{Files: f})
	if err != nil {
		logger.Warn(err)
	}

	logger.Printf("RestartIn(): exiting")
	os.Exit(0)
}

//exit this process after given wait time in seconds
func DieIn(waitn int64) {
	logger.Printf("DieIn(%v secs)", waitn)
	time.Sleep(time.Duration(waitn)*time.Second)
	logger.Printf("DieIn(): exiting")
	os.Exit(0)
}
