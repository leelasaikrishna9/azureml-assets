#!/bin/bash
# Hotfix for MMS breaking change AZUREML_MODEL_DIR 
# https://msdata.visualstudio.com/Vienna/_git/model-management/commit/4bd276623e64a4bf3ad9b3031cec730da8c44212?refName=refs%2Fheads%2Fmaster&_a=compare&path=%2Fsrc%2FProduct%2FCommon%2FServices%2FCommon.Services%2FUtilities%2FModel%2FModelUtility.cs
tritonrun=/var/runit/triton/run
declare -i l=$(perl -nle 'm{^MODEL_DIR=/var/azureml-app/} && print $.' $tritonrun)
if (( l==0 )); then exit; fi

tmpfile=/tmp/tritonrun

# Copy first half of the file
let n=$(wc -l < $tritonrun)
let h=(l-1)
sed -n "1,${h}p" $tritonrun > $tmpfile
echo 'cd "${AML_APP_ROOT:-/var/azureml-app}"' >> $tmpfile
echo 'MODEL_DIR=${AZUREML_MODEL_DIR}' >> $tmpfile
let l+=1
sed -n "${l},${n}p" $tritonrun >> $tmpfile
mv $tmpfile $tritonrun
chmod 755 $tritonrun