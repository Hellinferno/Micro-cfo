#!/usr/bin/env node

const path = require("path");
const { spawnSync } = require("child_process");

const args = process.argv.slice(2);
const command = args[0] || "build";
const passThroughArgs = args.slice(1);

const viteCommand = process.platform === "win32" ? "vite.cmd" : "vite";
const vitePath = path.resolve(__dirname, "..", "..", "node_modules", ".bin", viteCommand);

function runVite(viteArgs) {
  const result = spawnSync(vitePath, viteArgs, { stdio: "inherit" });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  process.exit(result.status ?? 0);
}

switch (command) {
  case "build":
    runVite(["build", ...passThroughArgs]);
    break;
  case "start":
  case "dev":
    runVite(["dev", ...passThroughArgs]);
    break;
  case "test":
    console.error("react-scripts test is not configured for this Vite project.");
    process.exit(1);
    break;
  case "eject":
    console.error("react-scripts eject is not supported for this Vite project.");
    process.exit(1);
    break;
  default:
    runVite([command, ...passThroughArgs]);
}
