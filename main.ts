// news-image-20261124 — the entry program (Node 22, standard library only).
//
// The front page is the file entry.png next to this program; the program's
// only job is to put a copy of it where the grader looks for it. The
// picture is located from this file's own URL, so the working directory the
// program is started from makes no difference.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const picture = join(here, "entry.png");
const target = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(target, { recursive: true });
copyFileSync(picture, join(target, "entry.png"));
console.log("wrote " + join(target, "entry.png"));
