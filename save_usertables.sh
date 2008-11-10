#/bin/bash

database_name=$1 
usersdump_file=$2
userschema_file=../userdata.sql

user_tables=`grep "CREATE TABLE" $userschema_file | sed "s/CREATE TABLE \(.*\)(.*/\1/"`  #something like "users petitions signatories"
t_user_tables=`echo $user_tables | sed "s/ / -t /g"`    # "users -t petitions -t signatories"

pg_dump -f $usersdump_file -F t -t $t_user_tables $database_name

if [ $? = 0 ]; then
    user_tables=`echo $user_tables | sed "s/ / , /g"`
    echo "DROP TABLE IF EXISTS $user_tables CASCADE ;" | psql $database_name
    echo Saved $user_tables of database $database_name into $usersdump_file ...
fi
