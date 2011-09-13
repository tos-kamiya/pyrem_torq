#!/usr/bin/bash

TA="/usr/bin/python ./tinyawk.py"

rm ./addlinenum.output
if $TA -f ./addlinenum.awk ./addlinenum.awk > ./addlinenum.output
then
  echo 
else
  es=$?
  echo "fail in addlinenum test"
  exit $es
fi

rm ./countcomment.output
if $TA -f ./countcomment.awk ./countcomment.awk > ./countcomment.output
then
  echo 
else
  es=$?
  echo "fail in countcomment test"
  exit $es
fi

rm printfibo.output
if $TA -f ./printfibo.awk > ./printfibo.output
then
  echo 
else
  es=$?
  echo "fail in printfibo test"
  exit $es
fi

rm removedup.output
if $TA -f ./removedup.awk ./removedup.awk > ./removedup.output
then
  echo 
else
  es=$?
  echo "fail in removedup test"
  exit $es
fi

rm wc.output
if $TA -f ./wc.awk ./wc.awk > ./wc.output
then
  echo 
else
  es=$?
  echo "fail in wc test"
  exit $es
fi

hg diff ./addlinenum.output
hg diff ./countcomment.output
hg diff ./printfibo.output
hg diff ./removedup.output
hg diff ./wc.output

