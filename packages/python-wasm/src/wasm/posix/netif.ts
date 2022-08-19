/*
Functions from net/if.h

NOTE: node.js has require('os').networkInterfaces(), but it is not equivalent
to the system calls in net/if.h.  E.g., on my mac if_indextoname(2) is "gif0",
but "gif0" isn't in require('os').networkInterfaces().  This is because
networkInterface "Returns an object containing network interfaces that
have been assigned a network address." and gif0 hasn't been.
*/

import { notImplemented } from "./util";
import constants from "./constants";

export default function netif({ posix, recv, send }) {
  return {
    // char *if_indextoname(unsigned int ifindex, char *ifname);
    if_indextoname: (ifindex: number, ifnamePtr: number): number => {
      const { if_indextoname } = posix;
      if (if_indextoname == null) {
        notImplemented("if_indextoname");
      }
      let ifname;
      try {
        ifname = if_indextoname(ifindex);
      } catch (_err) {
        return 0;
      }
      send.string(ifname, {
        ptr: ifnamePtr,
        len: constants.IFNAMSIZ,
      });
      return ifnamePtr;
    },

    // unsigned int if_nametoindex(const char *ifname);
    if_nametoindex: (ifnamePtr: number): number => {
      const { if_nametoindex } = posix;
      if (if_nametoindex == null) {
        notImplemented("if_nametoindex");
      }
      const ifname = recv.string(ifnamePtr);
      try {
        return if_nametoindex(ifname);
      } catch (_err) {
        return 0;
      }
    },
  };
}
