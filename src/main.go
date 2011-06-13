/*
   Copyright (C) 2003-2010 Institute for Systems Biology
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
	"flag"
)


//////////////////////////////////////////////
//main method
func main() {

	flag.BoolVar(&isMaster, "m", false, "Start as master node.")
	var atOnce int
	flag.IntVar(&atOnce, "n", 3, "For client nodes, the number of procceses to allow at once.")
	var hostname string
	flag.StringVar(&hostname, "hostname", "localhost:8083", "The address and port of/at wich to start the master.")
	var unsecure bool
	flag.BoolVar(&unsecure, "unsecure", false, "Don't use tls security.")
	var password string
	flag.StringVar(&password, "p", "", "The password to require with job submission.")
	flag.BoolVar(&verbose, "-v", false, "Use verbose logging.")

	flag.Parse()
	if unsecure {
		useTls = false
	}

	switch isMaster {
	case true:
		m := NewMaster()
		m.RunMaster(hostname, password)
	default:
		RunNode(atOnce, hostname)
	}

}
