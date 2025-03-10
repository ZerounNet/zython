import "xterm/css/xterm.css";
import { Terminal } from "xterm";
import setTheme from "./theme";
import python from "python-wasm";

export default async function terminal(element: HTMLDivElement) {
  (window as any).python = python;
  console.log("Calling python.init...");
  const t = new Date();
  await python.init();
  console.log("python.init done; time = ", new Date().valueOf() - t.valueOf());
  await python.exec("import readline");
  console.log('readline = ', await python.repr("readline"));
  const term = new Terminal({ convertEol: true });
  term.open(element);
  // @ts-ignore
  element.children[0].style.padding = "15px";
  term.resize(128, 40);
  setTheme(term, "solarized-light");
  term.onData((data) => {
    python.wasm.writeToStdin(data);
  });
  python.wasm.on("stdout", (data) => {
    term.write(data);
  });
  python.wasm.on("stderr", (data) => {
    term.write(data);
  });
  console.log("starting terminal");
  const r = await python.wasm.terminal();
  console.log("terminal terminated", r);
}
