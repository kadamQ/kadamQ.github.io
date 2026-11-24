#!/usr/bin/env bash
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HADOOP_HOME="${HADOOP_HOME:-$HOME/hadoop-3.5.0}"
test -d "$HADOOP_HOME/etc/hadoop" || { echo "Hadoop installation not found: $HADOOP_HOME" >&2; exit 1; }
JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")"
for name in core-site.xml hdfs-site.xml mapred-site.xml yarn-site.xml; do
  target="$HADOOP_HOME/etc/hadoop/$name"
  if [ -f "$target" ] && [ ! -f "$target.week9-original" ]; then
    cp "$target" "$target.week9-original"
  fi
  cp "$LAB/config/$name" "$target"
done
if ! grep -Fq '# WEEK9 JAVA HOME' "$HADOOP_HOME/etc/hadoop/hadoop-env.sh"; then
  printf '\n# WEEK9 JAVA HOME\nexport JAVA_HOME="%s"\n' "$JAVA_HOME" >> "$HADOOP_HOME/etc/hadoop/hadoop-env.sh"
fi
if ! grep -Fq '# >>> WEEK9 HADOOP >>>' "$HOME/.bashrc" 2>/dev/null; then
  cat >> "$HOME/.bashrc" <<'ENV'
# >>> WEEK9 HADOOP >>>
export HADOOP_HOME="$HOME/hadoop-3.5.0"
export JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")"
export HADOOP_MAPRED_HOME="$HADOOP_HOME"
export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"
# <<< WEEK9 HADOOP <<<
ENV
fi
echo 'Configuration saved. Run source ~/.bashrc.'
