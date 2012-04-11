#!/bin/bash

lang="python"
no_opt=0
opt=0
flow=0

function usage {
    echo "$0 [OPTIONS]"
    echo "  -lcython   select cython backend"
    echo "  -lpython   select python backend"
    echo "        -a   run all tests (-n -o -f)"
    echo "        -n   run tests without optimisations"
    echo "        -o   run tests with optimisations"
    echo "        -f   run tests with flow optimisations"
    echo " --help -h   show this message"
    exit 0
}

log_file=run_tests.log
echo -n > $log_file

for arg in $*
do
    case "$arg" in
	"-lcython")
	    lang="cython" ;;
	"-lpython")
	    lang="python" ;;
	"-a")
	    no_opt=1
	    opt=1
	    flow=1
	    ;;
	"-n")
	    no_opt=1 ;;
	"-o")
	    opt=1 ;;
	"-f")
	    flow=1 ;;
	"--help")
	    usage ;;
	"-h")
	    usage ;;
    esac
done

# echo ${lang} ${no_opt} ${opt} ${flow}

# no opt cases

declare -a failed_n=()
declare -a failed_o=()
declare -a failed_f=()

case_num=0

function print_job() {
    num=$1
    file=$2
    perspective=$3
    case_num=$((case_num+1))
    echo -ne "\r\033[K[${case_num}] running ${file} ${perspective}"
    echo "[${case_num}] running ${file} ${perspective}" >> $log_file
}

function check_err() {
    ret=$?
    step=$1
    file=$2
    decor=$3
    if [[ $ret != 0 ]]; then
	echo -ne "\n${step} failed ${file} ${decor}"; exit -1
    fi
}

if [[ $no_opt == 1 ]]
then
    for file in `ls -1`
    do
	file_compiled=0
        # module cases
	if [[ "${file}" =~ case_.*.py$ ]]
	then
	    print_job $case_num $file "(no opt)"
	    model_file=${file//.py/}
	    neco-compile -l $lang -m $model_file -I ../common 2> /dev/null > /dev/null
	    check_err "compilation" ${file} "(no_opt)"
	    file_compiled=1

	elif [[ "${file}" =~ case_.*.abcd$ ]]
	then
	    print_job $case_num $file "(no opt)"
	    model_file=${file}
	    neco-compile -l $lang --abcd $model_file -I ../common 2> /dev/null > /dev/null
	    check_err "compilation" ${file} "(no_opt)"
	    file_compiled=1
	fi

	if [[ file_compiled -eq 1 ]]
	then
	    expect_file=${model_file/.abcd/}_out
	    result_file=${model_file/.abcd/}_res

	    neco-explore -d ${result_file} 2> /dev/null > /dev/null
	    check_err "Exploration" ${file} "(no_opt)"
	    python compare.py ${model_file} ${expect_file} ${result_file}
	    case $? in
		2)
		    echo "fatal error occured in compare.py"; exit -1 ;;
		1)
		    echo "test ${model_file} failed_n" >> $log_file
		    failed_n[${#failed_n[*]}]=${model_file} ;;
		0)
		    echo "test ${model_file} passed" >> $log_file ;;
	    esac
	fi
    done;
fi

if [[ $opt == 1 ]]
then
    for file in `ls -1`
    do
	file_compiled=0
        # module cases
	if [[ "${file}" =~ case_.*.py$ ]]
	then
	    print_job $case_num $file "(opt)"
	    model_file=${file//.py/}
	    neco-compile -O -l $lang -m $model_file -I ../common 2> /dev/null > /dev/null
	    check_err "compilation" ${file} "(opt)"
	    file_compiled=1

	elif [[ "${file}" =~ case_.*.abcd$ ]]
	then
	    print_job $case_num $file "(opt)"
	    model_file=${file}
	    neco-compile -O -l $lang --abcd $model_file -I ../common 2> /dev/null > /dev/null
	    check_err "compilation" ${file} "(opt)"
	    file_compiled=1
	fi

	if [[ file_compiled -eq 1 ]]
	then
	    expect_file=${model_file/.abcd/}_out
	    result_file=${model_file/.abcd/}_res
	    neco-explore -d ${result_file} 2> /dev/null > /dev/null
	    check_err "Exploration" ${file} "(opt)"

	    python compare.py ${model_file} ${expect_file} ${result_file}
	    case $? in
		2)
		    echo "fatal error occured in compare.py"; exit -1 ;;
		1)
		    echo "test ${model_file} failed_n" >> $log_file
		    failed_n[${#failed_n[*]}]=${model_file} ;;
		0)
		    echo "test ${model_file} passed" >> $log_file ;;
	    esac
	fi
    done;
fi

if [[ $flow == 1 ]]
then
    for file in `ls -1`
    do
	file_compiled=0
        # module cases
	if [[ "${file}" =~ case_flow.*.py$ ]]
	then
	    print_job $case_num $file "(flow)"
	    model_file=${file//.py/}
	    neco-compile -Of -l $lang -m $model_file -I ../common 2> /dev/null > /dev/null
	    check_err "compilation" ${file} "(flow)"
	    file_compiled=1

	elif [[ "${file}" =~ case_flow.*.abcd$ ]]
	then
	    print_job $case_num $file "(flow)"
	    model_file=${file}
	    neco-compile -Of -l $lang --abcd $model_file -I ../common 2> /dev/null > /dev/null
	    check_err "compilation" ${file} "(flow)"
	    file_compiled=1
	fi

	if [[ file_compiled -eq 1 ]]
	then
	    expect_file=${model_file/.abcd/}_out
	    result_file=${model_file/.abcd/}_res
	    neco-explore -d ${result_file} 2> /dev/null > /dev/null
	    check_err "Exploration" ${file} "(flow)"

	    python compare.py ${model_file} ${expect_file} ${result_file}
	    case $? in
		2)
		    echo "fatal error occured in compare.py"; exit -1 ;;
		1)
		    echo "test ${model_file} failed_n" >> $log_file
		    failed_n[${#failed_f[*]}]=${model_file} ;;
		0)
		    echo "test ${model_file} passed" >> $log_file ;;
	    esac
	fi
    done;
fi



if [[ ${#failed_n[*]} > 0 ]]
then
    echo "Failed tests (no opt)"
    for ((i=0; i<${#failed_n[*]}; i++))
    do
	echo "${failed_n[$i]}"
    done
fi
if [[ ${#failed_o[*]} > 0 ]]
then
    echo "Failed tests (opt)"
    for ((i=0; i<${#failed_n[*]}; i++))
    do
	echo "${failed_n[$i]}"
    done
fi
if [[ ${#failed_f[*]} > 0 ]]
then
    echo "Failed tests (flow)"
    for ((i=0; i<${#failed_n[*]}; i++))
    do
	echo "${failed_n[$i]}"
    done
fi

failures_n=${#failed_n[*]}
failures_o=${#failed_o[*]}
failures_f=${#failed_f[*]}

success=$((case_num - failures_n - failures_o - failures_f))
failures=$((failures_n + failures_o + failures_f))

echo -e "\r\033[KPassed: ${success} \t Failed: ${failures}"
