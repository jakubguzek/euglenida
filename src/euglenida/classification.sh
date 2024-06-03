#!/usr/bin/env bash

qiime_path=$1
clssifier_path=$2
input_reads=$3
ouput_classification=$4
tmpdir=$5

verbose=$6

if [ $verbose -eq 1 ]; then
  echo "classifier.sh parameters:"
  echo "    qiime path                : $qiime_path"
  echo "    classifier path           : $clssifier_path"
  echo "    input reads path          : $input_reads"
  echo "    ouput classification path : $ouput_classification"
  echo "setting TMPDIR to $tmpdir"
fi

export TMPDIR=$tmpdir

if [ $verbose -eq 1 ]; then
  echo $TMPDIR
fi

$qiime_path feature-classifier classify-sklearn \
  --i-classifier $clssifier_path \
  --i-reads $input_reads \
  --o-classification $ouput_classification
