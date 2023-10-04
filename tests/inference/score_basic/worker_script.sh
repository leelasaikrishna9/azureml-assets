azmlinfsrv_procs=( $(ps -ef | grep '[a]zmlinfsrv' | awk '{print $2}') )
echo "worker num:" "$((${#azmlinfsrv_procs[@]} - 1))"