import terminal from "./terminal";

const element = document.createElement("div");
document.body.appendChild(element);
document.body.style.margin = "0px";

async function main() {
    element.innerHTML = "";
    await terminal(element);
}

main();
