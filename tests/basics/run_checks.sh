#!/bin/bash
VERBOSE=0
HIDE_STDERR=1

OPT_CASES="`ls case_*.py 2> /dev/null | grep _OPT` `ls case_*.abcd 2> /dev/null | grep _OPT`"
NOPT_CASES="`ls case_*.py 2> /dev/null | grep _NOPT` `ls case_*.abcd 2> /dev/null | grep _NOPT`"
BPACK_CASES="`ls case_*.py 2> /dev/null | grep _BPACK` `ls case_*.abcd 2> /dev/null | grep _BPACK`"
FLOW_CASES="`ls case_*.py 2> /dev/null | grep _FLOW` `ls case_*.abcd 2> /dev/null | grep _FLOW`"

RAN_CASES=0
PASSED_CASES=0
FAILED_CASES=0
SKIPPED_CASES=0
CHECKED_FORMULAS=0
START_TIME=$(date +%s)

FAILURES=/tmp/neco_run_failures$$.tmp
touch $FAILURES

function cleanup {
  rm -f $FAILURES
}
trap cleanup EXIT

if [ $HIDE_STDERR = 1 ]
then
    exec 2> stderr
fi

run_case() {
    RAN_CASES=$(($RAN_CASES + 1))
}

check_formula() {
    CHECKED_FORMULAS=$(($CHECKED_FORMULAS + 1))
}

skip_case() {
    SKIPPED_CASES=$(($SKIPPED_CASES + 1))
}

passed_case() {
    PASSED_CASES=$(($PASSED_CASES + 1))
}

failed_case() {
    MODEL=$1
    FORMULA=$2
    COMPILE_OPTIONS=$3
    CHECKER_OPTIONS=$4
    NECOSPOT_OPTIONS=$5
    EXPECTED=$6
    echo "--------------------------------------------------------------------------------" >> $FAILURES
    echo " Failure: $MODEL"  >> $FAILURES
    echo " Formula: $FORMULA"  >> $FAILURES
    echo " Complile options: $COMPILE_OPTIONS"  >> $FAILURES
    echo " Checker options: $CHECKER_OPTIONS"  >> $FAILURES
    echo " NecoSpot options: $NECOSPOT_OPTIONS"  >> $FAILURES
    echo " Expected: $EXPECTED" >> $FAILURES
    FAILED_CASES=$(($FAILED_CASES + 1))
}

execution_time() {
    END_TIME=$(date +%s)
    echo "$(( $END_TIME - $START_TIME ))"
}

print_stats() {
    cat $FAILURES
    echo "--------------------------------------------------------------------------------"
    echo "checked $CHECKED_FORMULAS formulas in `execution_time` seconds"
    echo "$PASSED_CASES passed"
    echo "$SKIPPED_CASES skipped"
    echo "$FAILED_CASES failed"
}

name() {
    echo $1 | sed 's/\(case_\|_FLOW\|_OPT\|_NOPT\|_BPACK\|\.py\|\.abcd\)//g'
}

is_abcd() {
    echo $1 | grep "\.abcd" > /dev/null
}

is_py() {
    echo $1 | grep "\.py" > /dev/null
}

verbose() {
    if [ $VERBOSE = 1 ]
    then
        echo $@
    fi
}

info_begin() {
    if [ $VERBOSE = 1 ]
    then
        echo
        echo "********************************************************************************"
        echo "$1"
        echo "********************************************************************************"
    fi
}

info_end() {
    if [ $VERBOSE = 1 ]
    then
        echo "********************************************************************************"
        echo
    fi
}

extract_options() {
    NECO_FILE=$1
    OPTIONS=""
    TMP_FILE1=__neco_tmp1__$$
    TMP_FILE2=__neco_tmp2__$$
    touch $TMP_FILE1 $TMP_FILE2
    grep "#" $NECO_FILE > $TMP_FILE1
    sed s/\#// $TMP_FILE1 > $TMP_FILE2
    while read LINE
    do
        OPTIONS="$OPTIONS $LINE"
    done < $TMP_FILE2
    rm -f $TMP_FILE1 $TMP_FILE2
    echo $OPTIONS
}

compile_model() {
    MODEL=$1
    OPTIONS=$2

    rm -f net.so

    if is_abcd $MODEL
    then
        # verbose "[E] ABCD, not implemented yet"
        neco-compile --abcd "$MODEL" $OPTIONS > /dev/null
    elif is_py $MODEL
    then
        neco-compile -m "$MODEL" $OPTIONS > /dev/null
    fi
}

run_tests() {
    CASES=$1
    COMPILE_OPTIONS=$2
    CHECKER_OPTIONS=$3
    NECOSPOT_OPTIONS=$4

    COMPILE_OPTIONS="$COMPILE_OPTIONS -lcython"

    for CASE in $CASES
    do
        run_case
        echo -n ":"
        NAME=`name $CASE`
        LTL_FILE="case_$NAME.ltl"

        ################################################################################
        info_begin "case $NAME"
        ################################################################################

        if [ ! -f $LTL_FILE ]
        then
            verbose "skipping '$NAME', no ltl file."
            info_end
            skip_case
            continue
        fi

        compile_model "$CASE" "$COMPILE_OPTIONS"

        # check formulas
        exec 5< $LTL_FILE
        while read FORMULA <&5
        do
            if [ "$FORMULA" = "" ] || [[ "$FORMULA" = \#* ]]
            then
                continue
            fi
            read EXPECTED <&5
            rm -f checker.so neco_formula

            if [ "$EXPECTED" = "OK" ]
            then
                EXPECTED="no counterexample found"
            elif [ "$EXPECTED" = "KO" ]
            then
                EXPECTED="a counterexample exists (use -C to print it)"
            else
                echo -e "\n[E] bad entry in $LTL_FILE ($FORMULA - $EXPECTED)"
                continue
            fi

            check_formula

            echo -n "."
            verbose -n "checking formula \"$FORMULA\"... "

            # compile checker
            neco-check --formula "$FORMULA" $CHECKER_OPTIONS > /dev/null
            if [ $? != 0  ]
            then
                echo -e "\nneco-check error"
                failed_case "$CASE" "$FORMULA" "$COMPILE_OPTIONS" "$CHECKER_OPTIONS" "$NECOSPOT_OPTIONS"
                verbose failure
                continue
            fi
            verbose "neco-check success"

            # extract options
            OPTIONS=`extract_options neco_formula`
            OPTIONS="$NECOSPOT_OPTIONS $OPTIONS"
            # run neco spot
            NS_OUT=/tmp/neco_run_test$$.tmp
            neco-spot $OPTIONS neco_formula > $NS_OUT
            RES=`tail -n 1 $NS_OUT`
            if [ "$RES" = "$EXPECTED" ]
            then
                passed_case
                verbose ok
            else
                failed_case "$CASE" "$FORMULA" "$COMPILE_OPTIONS" "$CHECKER_OPTIONS" "$NECOSPOT_OPTIONS" "$EXPECTED"
                verbose failure
            fi
            rm $NS_OUT
        done
        exec 5<&-
        ################################################################################
        info_end
        ################################################################################
    done
}

echo -e "running NOPT cases"
run_tests "$NOPT_CASES" "" "" ""
echo -e "\nrunning OPT cases"
run_tests "$OPT_CASES" "-O" "" ""
echo -e "\nrunning BPACK cases"
run_tests "$BPACK_CASES" "-O -Op" "" ""
echo -e "\nrunning FLOW cases"
run_tests "$FLOW_CASES" "-O -Op -Of" "" ""
echo

#MODEL="case_FlowAbcd2_NOPT_OPT_BPACK_FLOW.abcd"
#echo -e "running NOPT cases"
#run_tests "$MODEL" "" "" ""
#echo -e "\nrunning OPT cases"
#run_tests "$MODEL" "-O" "" ""
#echo -e "\nrunning BPACK cases"
#run_tests "$MODEL" "-O -Op" "" ""
#echo -e "\nrunning FLOW cases"
#run_tests "$MODEL" "-O -Op -Of" "" ""

print_stats
