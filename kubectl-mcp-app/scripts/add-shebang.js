#!/usr/bin/env node

import { readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const mainFile = join(__dirname, "..", "dist", "main.js");

try {
  const content = readFileSync(mainFile, "utf-8");

  if (!content.startsWith("#!/usr/bin/env node")) {
    writeFileSync(mainFile, `#!/usr/bin/env node\n${content}`);
    console.log("Added shebang to dist/main.js");
  } else {
    console.log("Shebang already present in dist/main.js");
  }
} catch (error) {
  console.error("Error adding shebang:", error.message);
  process.exit(1);
}
