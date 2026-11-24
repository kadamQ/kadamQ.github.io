# Optional Python 3 Hadoop Streaming lab

Hadoop Streaming runs batch MapReduce jobs through a line-oriented interface.
The mapper and reducer can be written in a language other than Java. A process
reads its input channel, **standard input (`stdin`)**, and writes result records
to **standard output (`stdout`)**. A separate diagnostics channel, **standard
error (`stderr`)**, carries counters and error messages. Hadoop still handles
input splits, task execution, shuffle, grouping and output. Each mapper or
reducer task starts its process when initialized; that process handles many
records.

## Requirements

Complete the main lesson's Hadoop/WSL2 setup and HDFS input upload first. The
original WordCount files must already be in `/week9/input`. These commands run
in **Bash in Ubuntu/WSL2** from the repository's `bigdata/hadoop/lab/streaming`
directory. Python 3 must be installed and available as `python3` on every worker
that executes a task, including the one worker in the local teaching setup.
If it is missing in Ubuntu, install it with `sudo apt install python3`.
There are no third-party Python packages.

```bash
cd ~/bigdata-course/bigdata/hadoop/lab/streaming
python3 --version
set -o pipefail
```

The explicit `python3 script.py` commands do not require executable file bits.
Hadoop's `-files` option distributes the scripts to task working directories;
it does not install the Python interpreter. Generic options (`-D`, `-files`)
must precede Streaming options such as `-input` and `-mapper`.

## 1. WordCount locally

The mapper preserves the Java example's case and punctuation. Its separators
are exactly Java `StringTokenizer`'s defaults: space, tab, line feed, carriage
return and form feed. `Hadoop` and `hadoop` are different keys. The default
Streaming protocol uses the first tab to separate the key from its value.

```bash
cat ../data/input-1.txt ../data/input-2.txt \
  | python3 mapper.py \
  | LC_ALL=C sort -t $'\t' -k1,1 \
  | python3 reducer.py > wordcount-local.tsv
cat wordcount-local.tsv
diff -u ../data/expected-output.txt wordcount-local.tsv
```

Expected output (the separators are tabs):

```text
data	1
hadoop	2
spark	2
```

The local sort groups the first tab-delimited field. Hadoop performs its own
shuffle and sort in the cluster job. The reducer emits a group when the key
changes and emits the last group after input ends. Empty input produces no
records. A successful `diff` prints nothing.

## 2. WordCount on Hadoop

Keep the HDFS and YARN services from the main lesson running. Each submission
uses a new output path; Hadoop output directories must not already exist.

```bash
streaming_wordcount_output="/week9/streaming-wordcount-$(date +%Y%m%d-%H%M%S)-$$"
mapred streaming \
  -D mapreduce.job.name=week9-python-wordcount \
  -D mapreduce.job.reduces=1 \
  -files mapper.py,reducer.py \
  -input /week9/input \
  -output "$streaming_wordcount_output" \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"
hdfs dfs -cat "$streaming_wordcount_output/part-*"
```

One reducer makes this small result easy to inspect in sorted order. Python
receives the input line text; with the default text input format, Hadoop's
byte-offset key is not sent to the Streaming mapper.

## 3. Grouped average extension

`data/response-times.csv` has the header `path,response_ms` and eight data rows.
Seven have a duration; the last `/courses` row has a missing value. The mapper
ignores exact header rows. All other records must satisfy this contract:

- Exactly two fields on **one physical line**. Ordinary quoted CSV fields are
  accepted; quoted fields spanning several physical lines are unsupported.
- The path begins with `/` and contains no tab, newline or control characters.
- The duration contains decimal digits only and represents nonnegative integer
  milliseconds. Zero is valid. Missing values, `NaN`, negatives, fractions and
  other invalid values are skipped; missing values never become zero.

Every blank or invalid input record increments the single counter
`StreamingLab.InvalidRecord` by writing
`reporter:counter:StreamingLab,InvalidRecord,1` to **stderr**. The sample produces
one such counter update. During local testing, this line appears in the
terminal; it is not part of the data written to stdout.

The mapper emits `path TAB duration TAB 1`. The first tab ends the key;
`duration TAB 1` is the value. `sum_count_combiner.py` adds both numeric fields
and emits the same `path TAB sum TAB count` protocol. The reducer imports its
validated grouping helper, then divides the final sum by the final count.
Keep all three extension scripts together, even when omitting the combiner
option. Malformed intermediate records, negative sums and nonpositive counts
cause a failing process rather than a misleading result.

Run without a combiner:

```bash
python3 latency_mapper.py < data/response-times.csv \
  | LC_ALL=C sort -t $'\t' -k1,1 \
  | python3 latency_reducer.py > average-local.tsv
cat average-local.tsv
diff -u data/expected-average.tsv average-local.tsv
```

Run one local combiner pass and compare:

```bash
python3 latency_mapper.py < data/response-times.csv \
  | LC_ALL=C sort -t $'\t' -k1,1 \
  | python3 sum_count_combiner.py \
  | python3 latency_reducer.py > average-combined.tsv
diff -u average-local.tsv average-combined.tsv
```

The expected output is `/courses` = `100.00`, `/library` = `60.00` and `/search`
= `40.00` milliseconds. For `/search`, `(10 + 20 + 90) / 3 = 40`. If a combiner
sees `10,20` and another sees `90`, they emit `(30,2)` and `(90,1)`. Summing
these pairs still gives `(120,3)`. Averaging their partial averages would give
`(15 + 90) / 2 = 52.5`, which is wrong because the groups have unequal sizes.
Hadoop may run a combiner zero, one or multiple times; sum/count pairs remain
valid under every such arrangement. Division belongs only in the reducer.

Submit the extension to Hadoop:

```bash
hdfs dfs -mkdir -p /week9/streaming-latency-input
hdfs dfs -put -f data/response-times.csv /week9/streaming-latency-input/
streaming_average_output="/week9/streaming-average-$(date +%Y%m%d-%H%M%S)-$$"
mapred streaming \
  -D mapreduce.job.name=week9-python-average \
  -D mapreduce.job.reduces=1 \
  -files latency_mapper.py,sum_count_combiner.py,latency_reducer.py \
  -input /week9/streaming-latency-input/response-times.csv \
  -output "$streaming_average_output" \
  -mapper "python3 latency_mapper.py" \
  -combiner "python3 sum_count_combiner.py" \
  -reducer "python3 latency_reducer.py" \
  -cmdenv PYTHONPATH=.
hdfs dfs -cat "$streaming_average_output/part-*"
```

The `-put -f` command replaces only this extension's named CSV input file when
you repeat the exercise. The WordCount input remains at `/week9/input`.
The Streaming option `-cmdenv PYTHONPATH=.` tells Python to look for imported
helper files in the task's working directory, where Hadoop makes them available.
Keep this option when submitting without `-combiner` as well.

## Official reference

[Apache Hadoop Streaming documentation](https://hadoop.apache.org/docs/r3.5.0/hadoop-streaming/HadoopStreaming.html)
describes the process and tab protocol, option ordering, file distribution,
combiner option and stderr counters. See also the
[MapReduce tutorial](https://hadoop.apache.org/docs/r3.5.0/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html)
for the surrounding job and task model.
