#!/bin/bash

function add_microsoft_header() {
    # put microsoft header in NOTICE.txt
    echo '----------------------------------------------------------------------------------
    THIRD PARTY SOFTWARE NOTICES AND INFORMATION
    Do Not Translate or Localize

    This software incorporates material from third parties. Microsoft
    makes certain open source code available at
    http://3rdpartysource.microsoft.com, or you may send a check or money
    order for US $5.00, including the product name, the open source
    component name, and version number, to:

    Source Code Compliance Team
    Microsoft Corporation
    One Microsoft Way
    Redmond, WA 98052
    USA

    Notwithstanding any other terms, you may reverse engineer this
    software to the extent required to debug changes to any libraries
    licensed under the GNU Lesser General Public License for your own use.

    ----------------------------------------------------------------------------------
    ' > NOTICE.txt
}

function add_nvidia_deeplearning_license() {
    echo "NVIDIA Deep Learning Container License" >> NOTICE.txt
    license=https://github.com/triton-inference-server/server/blob/main/NVIDIA_Deep_Learning_Container_License.pdf
    echo $license >> NOTICE.txt
    echo "" >> NOTICE.txt
}

# As of TritonServer:21.06-py3, TritonServer backend license are not found in the container.
# For now pull from github.
function add_tritonserver_backend_license() {
    local backend=$1
    local url=""
    
    # Find TritonServer NGC container version corresponding to TritonServer Release
    tritonRelease=$(</opt/tritonserver/TRITON_VERSION)
    ngcContainerVers=$(curl -sL https://github.com/triton-inference-server/server/releases \
        | perl -nle "m{Release ${tritonRelease} corresponding to NGC container ([\w\.]+)} && print \"r\$1\"")

    # Check LICENSE exists at URL
    testurl=https://raw.githubusercontent.com/triton-inference-server/${backend}_backend/${ngcContainerVers}/LICENSE
    if curl --output /dev/null --silent -r 0-0 --fail "${testurl}"; then
        url=${testurl}
    else
        # Try name LICENSE.md
        if curl --output /dev/null --silent -r 0-0 --fail "${testurl}.md"; then
            url=${testurl}.md
        else
            # Try main branch
            if curl --output /dev/null --silent -r 0-0 --fail "${testurl/${ngcContainerVers}/main}"; then
                url="${testurl/${ngcContainerVers}/main}"
            elif curl --output /dev/null --silent -r 0-0 --fail "${testurl/${ngcContainerVers}/main}.md"; then
                # Try main branch with filename LICENSE.md
                url="${testurl/${ngcContainerVers}/main}.md"
            fi
        fi
    fi
    if [ ! -z $url ]; then
        echo "==> tritonserver/${backend}_backend <==" >> NOTICE.txt
        curl -sL $url >> NOTICE.txt
        echo "" >> NOTICE.txt
    fi
}

# Utility.  Pull License from URL
function add_remote_license() {
    local pkgheader=$1
    local url=$2

    if curl --output /dev/null --silent -r 0-0 --fail "${url}"; then
        echo "==> $pkgheader <==" >> NOTICE.txt
        curl -sL $url >> NOTICE.txt
        echo "" >> NOTICE.txt
    fi
}

# Pull remote LICENSE for specific 1st order dependencies provided by Nvidia.
function add_tritonserver_remote_licenses() {

    add_remote_license "grpc/grpc"  https://raw.githubusercontent.com/grpc/grpc/master/LICENSE
    add_remote_license "nlohmann/json" https://raw.githubusercontent.com/nlohmann/json/develop/LICENSE.MIT 
    add_remote_license "libevent/libevent" https://raw.githubusercontent.com/libevent/libevent/master/LICENSE
    add_remote_license "prometheus-cpp" https://raw.githubusercontent.com/jupp0r/prometheus-cpp/master/LICENSE
    add_remote_license "google/crc32c" https://raw.githubusercontent.com/google/crc32c/main/LICENSE
    add_remote_license "googleapis/google-cloud-cpp" https://raw.githubusercontent.com/googleapis/google-cloud-cpp/main/LICENSE
    add_remote_license "Azure/azure-storage-cpplite" https://raw.githubusercontent.com/Azure/azure-storage-cpplite/master/LICENSE
    add_remote_license "aws/aws-sdk-cpp" https://raw.githubusercontent.com/aws/aws-sdk-cpp/main/LICENSE
    add_remote_license "intel/gmmlib" https://raw.githubusercontent.com/intel/gmmlib/master/LICENSE.md
    add_remote_license "intel/intel-graphics-compiler" https://raw.githubusercontent.com/intel/intel-graphics-compiler/master/LICENSE.md

    intel_compute_runtime_url=https://raw.githubusercontent.com/intel/compute-runtime/master/LICENSE.md
    if curl --output /dev/null --silent -r 0-0 --fail "${intel_compute_runtime_url}"; then
        echo "==> intel-igc-opencl <==" >> NOTICE.txt
        echo "==> intel-ocloc <==" >> NOTICE.txt
        echo "==> intel-opencl <==" >> NOTICE.txt
        curl -sL ${intel_compute_runtime_url} >> NOTICE.txt
        echo "" >> NOTICE.txt
    fi
}

# Add LICENSE files for tritonserver and tritonserver backends
function add_tritonserver_licenses() {

    # append header "==> tritonserver <==" and 
    #   1. Nvidia Deep Learning License
    #   2. tritonserver license
    echo "==> tritonserver <==" >> NOTICE.txt
    add_nvidia_deeplearning_license
    echo "" >> NOTICE.txt

    find  /opt/tritonserver -maxdepth 1 -type f -name LICENSE\* -exec tail -v -n +1 {} + \
        | perl -nle '!m{==>\s+} && print "$_"' \
        >> NOTICE.txt
    echo "" >> NOTICE.txt

    # Add EULA for CUDA
    echo "==> cuda-compat-11 <==" >> NOTICE.txt
    echo https://docs.nvidia.com/cuda/pdf/EULA.pdf >> NOTICE.txt
    echo "" >> NOTICE.txt

    # Add EULA for cuDNN
    echo "==> libcudnn8 <==" >> NOTICE.txt
    echo "==> libcudnn8-dev <==" >> NOTICE.txt
    echo https://docs.nvidia.com/deeplearning/cudnn/pdf/cuDNN-SLA.pdf >> NOTICE.txt
    echo "" >> NOTICE.txt

    # For certain OSS dependencies, provided by Nvidia, whose licenses are not
    # discovered in tritonserver container by current script (generate_notice.sh),
    # pull a remote copy of the license.
    add_tritonserver_remote_licenses

    # append header and license for tritonserver backend connector layers
    for backend in $(find /opt/tritonserver/backends -maxdepth 1 -mindepth 1 -type d -exec basename {} \; ); do
        if [[ $backend =~ tensorflow([0-9]) ]]; then 
            let v=${BASH_REMATCH[1]}; 
            if (( v!=1 )); then continue; fi
            backend=tensorflow
        fi
        add_tritonserver_backend_license $backend
    done
    add_tritonserver_backend_license tensorrt
    
    # append header and license for tritonserver backend frameworks
    find  /opt/tritonserver/backends -type f -name LICENSE\* -exec tail -v -n +1 {} + \
        |   perl -nle 'm{(==>\s+)/opt/(.+)/LICENSE\S*(\s+<==)} ? print "\n$1$2$3"  : print "$_" ' \
        >> NOTICE.txt

    echo "" >> NOTICE.txt
}

function add_other_miniconda_licenses() {
    # for each file under /opt/miniconda whose name contains "LICENSE"
    # excluding the miniconda license we already added
    #   1. add header "==> package_name-package_version <==" above each license
    #   2. append header + license to NOTICE.txt
    find /opt/miniconda -mindepth 2 -type f -regex ".*LICENSE.*" \
            -exec tail -v -n +1 {} + \
        | sed "s/.*\/lib\//==> /" \
        | sed "s/.*site-packages\//==> /" \
        | sed "s/\/LICENSE.*/ <==/" \
        | sed "s/\.dist-info//" \
        | sed "s/conda\/_vendor\///" \
        >> NOTICE.txt
    echo "" >> NOTICE.txt
}

function add_miniconda_licenses() {
    # append header "==> Miniconda <==" and the miniconda license to NOTICE.txt
    echo "==> miniconda <==" >> NOTICE.txt
    miniconda_license=/opt/miniconda/LICENSE.txt
    cat $miniconda_license >> NOTICE.txt
    echo "" >> NOTICE.txt
    add_other_miniconda_licenses
}

# Add LICENSE files for addon software under /opt
function add_addon_sw_licenses() {
    local addon=$1

    find  /opt/${addon} -name LICENSE\* -a -type f -a -exec tail -v -n +1 {} + \
        |   perl -nle 'm{(==>\s+)/opt/(.+)/LICENSE\S*(\s+<==)} ? print "$1$2$3"  : print "$_" ' \
        >> NOTICE.txt

    echo "" >> NOTICE.txt 
}

function add_other_licenses() {
    # for each file under /usr whose name starts with "LICENSE"
    #   append header and license to NOTICE.txt
    find -L /usr  -name LICENSE\* -a -type f \
            -exec tail -v -n +1 {} + \
        | perl -nle 'm{(==>\s*/usr/.+)/LICENSE\S*(\s+<==)} ? print "$1$2"  : print "$_" ' \
        | perl -nle 'm{(==>\s*)/usr/.*/(?:lib/)?(.+<==)} ? print "$1$2"  : print "$_" ' \
        | sed "s/\.dist-info//" \
        >> NOTICE.txt
    echo "" >> NOTICE.txt
}

function add_copyright_files() {
    # The copyright files for multiple OSS packages may be linked to 
    # the same file (i.e. Linux inode).
    # For each path under /usr/share/doc ending in "copyright",
    # the find command below prints the inode and the absolute path.
    # Option -L directs find command to include symbolic links in the search traversal.
    # 
    # As bash does not support multi-dimensional array, jq is used to build dictionary
    # { inode1: [ pkg1, pkg2, pkg3 ], ... inodeN: [ pkgx, pkgy, pkgz ] }
    pkgsHashFile=/tmp/copyright_pkgs.json
    copyrightsInumFile=copyrights_inum.txt
    find -L /usr/share/doc -iname \*copyright -exec ls -i {} + > ${copyrightsInumFile}
    # We use perl here as it is already installed in tritonserver container image.
    # awk doesn't support extended regex and gawk is not installed at the time of writing (tritonserver:21.06-py3)
    # Equivalent gawk statemnent:
    # gawk -v pat="/usr/share/doc/(.+)/copyright" 'BEGIN{ OFS=","; } match($2, pat, m) { print $1, m[1] }' 
    cat ${copyrightsInumFile} \
        | perl -nle 'm{(\d+)\s+/usr/share/doc/(.+)/copyright$} && print "$1,$2"' \
        | jq -Rsn '[inputs| split("\n") | (.[] | select(length > 0) | split(",")) as $input | { ($input[0]) : [ { "component": ($input[1]) } ] }] ' \
        | jq 'reduce .[] as $e ({}; reduce ($e|keys)[] as $inum (.; .[$inum] += $e[$inum] ))' \
        | jq 'with_entries( .value |= map(.component) )' > ${pkgsHashFile}
    #
    # Finally, to generate NOTICE, list package names followed by the content of the copyright file.
    #
   for k in $(jq -r 'keys|.[]' ${pkgsHashFile} ); do
        echo "" >> NOTICE.txt
        unset components;
        readarray -t components < <(jq --arg i "$k" -c '.[$i]|.[]' ${pkgsHashFile})
        for comp in "${components[@]}"; do
            # Unquote package name in the header
            echo "==> $(echo $comp|tr -d '"') <==" >> NOTICE.txt
        done
        copyright=$(find /usr/share/doc -inum $k)
        if [  -f $copyright ]; then
            cat $copyright >> NOTICE.txt
        fi            
    done
    rm ${pkgsHashFile}
    rm ${copyrightsInumFile}
}

add_microsoft_header
for addon in $(find /opt -maxdepth 1 -mindepth 1 -type d -exec basename {} \; ); do
    if [ $addon == tritonserver ]; then
        add_tritonserver_licenses 
    elif [ $addon == miniconda ]; then
        add_miniconda_licenses
    else
        add_addon_sw_licenses $addon
    fi
done

add_other_licenses
add_copyright_files

