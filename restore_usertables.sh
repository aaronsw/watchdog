#/bin/bash

database_name=$1 
usersdump_file=$2

pg_restore $usersdump_file -d $database_name

if [ $? = 0 ]; then
    echo Restored user tables of database $database_name from $usersdump_file...
fi