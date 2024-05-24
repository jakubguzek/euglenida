#!/usr/bin/env bash
tar cvf euglenida.tar.gz -I "pigz --best" \
  ./src ./scripts ./LICENSE.md ./README.md ./setup.py ./setup.cfg ./requirements.txt
scp ./euglenida.tar.gz mstu5@212.87.6.113:/home/students/mstu5/project/
