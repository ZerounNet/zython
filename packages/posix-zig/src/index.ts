// Map from nodejs to zig descriptions:

const nodeToZig = {
  arm64: "aarch64",
  x64: "x86_64",
  linux: "linux-gnu",
  darwin: "macos",
};

const name = `${nodeToZig[process.arch]}-${nodeToZig[process.platform]}`;

interface Module {
  // unistd:
  chroot: (path: string) => void;
  getegid: () => number;
  geteuid: () => number;
  gethostname: () => string;
  getpgid: (number) => number;
  getppid: () => number;
  setpgid: (pid: number, pgid: number) => void;
  setregid: (rgid: number, egid: number) => void;
  setreuid: (ruid: number, euid: number) => void;
  setsid: () => number;
  setegid: (gid: number) => void;
  seteuid: (uid: number) => void;
  ttyname: (fd: number) => string;
}

let mod: Partial<Module> = {};
try {
  mod = require(`./${name}.node`);
  for (const name in mod) {
    exports[name] = mod[name];
  }
} catch (_err) {}

export default mod;
